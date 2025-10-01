#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# SCRIPT PARA ATUALIZACAO EM MASSA DAS GARANTIAS DELL - CORRIGIDO WINDOWS
# =============================================================================

import os
import sys
import pyodbc
import requests
import json
import time
import logging
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Configurar encoding para Windows
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

# Carregar variáveis de ambiente
load_dotenv()

# Configurar logging sem emojis
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dell_warranty_update.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configurações
SQL_SERVER = os.getenv('SQL_SERVER', 'CLOSQL02')
SQL_DATABASE = os.getenv('SQL_DATABASE', 'DellReports')
SQL_USERNAME = os.getenv('SQL_USERNAME')
SQL_PASSWORD = os.getenv('SQL_PASSWORD')
USE_WINDOWS_AUTH = os.getenv('USE_WINDOWS_AUTH', 'true').lower() == 'true'

DELL_CLIENT_ID = os.getenv('DELL_CLIENT_ID', 'l75c9d200744a444a08c54b666ddbd9b1a')
DELL_CLIENT_SECRET = os.getenv('DELL_CLIENT_SECRET', '5a6bfc5dd76c40a6bd8b896c6ab63e9e')

# --- Helper to chunk lists (used by the bulk updater/checker) ---
def chunk_list(data, size=100):
    """Divide uma lista em 'chunks' (blocos) de um tamanho especificado."""
    for i in range(0, len(data), size):
        yield data[i:i + size]


class DellWarrantyChecker:
    """
    Thread-safe checker que agrupa service tags em batches (até 100 por requisição)
    e processa esses batches em paralelo, retornando todos os resultados
    sem compartilhar uma lista mutável entre threads.

    Uso: instanciar com a lista de tags e chamar .run() que retorna a lista de resultados.
    """

    def __init__(self, servicetags_list, client_id=None, client_secret=None,
                 max_workers=10, batch_size=100, request_delay=0.0, request_timeout=30.0, max_retries=2):
        self.servicetags = [t.strip().upper() for t in servicetags_list if t and isinstance(t, str)]
        self.client_id = client_id
        self.client_secret = client_secret

        self.max_workers = max_workers
        self.BATCH_SIZE = batch_size
        self.request_delay = request_delay
        self.request_timeout = request_timeout
        self.max_retries = max_retries

        # token obtido via chamada ao endpoint de oauth da Dell
        self.api_token = self._get_auth_token()

        # agregação feita somente na thread principal (run)
        self.results = []

        # session por thread
        self._local = threading.local()

    def _get_auth_token(self):
        """Obtém token de acesso usando client_id/client_secret.
        Se client_id/secret não estiverem informados, retorna token vazio.
        Substitua a lógica conforme sua infra (cache do token, refresh, etc.).
        """
        if not self.client_id or not self.client_secret:
            logging.warning("Client ID/secret não informados — usando token vazio (apenas para testes)")
            return ''

        try:
            url = 'https://apigtwb2c.us.dell.com/auth/oauth/v2/token'
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            data = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }
            resp = requests.post(url, headers=headers, data=data, timeout=10)
            resp.raise_for_status()
            j = resp.json()
            token = j.get('access_token')
            if not token:
                logging.error('Token de autenticação não retornado pela Dell API')
                return ''
            return token
        except Exception as e:
            logging.exception('Falha ao obter token Dell: %s', e)
            return ''

    def _get_session(self):
        """Retorna uma requests.Session por thread (thread-local) com retries básicos."""
        if getattr(self._local, 'session', None) is None:
            s = requests.Session()
            try:
                from requests.adapters import HTTPAdapter
                from urllib3.util.retry import Retry
                retries = Retry(total=2, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])
                s.mount('https://', HTTPAdapter(max_retries=retries))
            except Exception:
                # urllib3 não disponível ou adapter já configurado
                pass
            self._local.session = s
        return self._local.session

    def process_warranty_batch(self, servicetags_batch):
        """Worker: processa um batch de service tags e RETORNA a lista de resultados.
        Não modifica estado compartilhado.
        """
        tags_string = ','.join(servicetags_batch)
        url = 'https://apigtwb2c.us.dell.com/PROD/sbil/eapi/v5/asset-entitlements'
        params = {'servicetags': tags_string}
        headers = {
            'Authorization': f'Bearer {self.api_token}' if self.api_token else '',
            'Accept': 'application/json'
        }

        session = self._get_session()

        attempt = 0
        while attempt <= self.max_retries:
            attempt += 1
            try:
                resp = session.get(url, headers=headers, params=params, timeout=self.request_timeout)
                resp.raise_for_status()
                data = resp.json()

                logging.info('Sucesso: lote de %d tags (attempt=%d)', len(servicetags_batch), attempt)

                # opcional: delay por batch para respeitar limites
                if self.request_delay > 0:
                    time.sleep(self.request_delay)

                # normalize: garantir que retornamos uma lista
                if isinstance(data, list):
                    return data
                elif data is None:
                    return []
                else:
                    return [data]

            except requests.RequestException as ex:
                logging.warning('Erro HTTP/Conn no lote (%d tags) attempt=%d: %s', len(servicetags_batch), attempt, ex)
                if attempt > self.max_retries:
                    logging.error('Falha definitiva no lote (%d tags): %s', len(servicetags_batch), ex)
                    return []
                time.sleep(0.5 * attempt)
            except Exception as ex:
                logging.exception('Erro inesperado ao processar lote (%d tags): %s', len(servicetags_batch), ex)
                return []

    def run(self):
        """Executa todos os batches em paralelo e agrega resultados localmente (thread principal)."""
        tags_batches = list(chunk_list(self.servicetags, self.BATCH_SIZE))
        if not tags_batches:
            logging.info('Nenhuma Service Tag para processar.')
            return []
        logging.info('Total Service Tags: %d, Batches: %d, Workers: %d', len(self.servicetags), len(tags_batches), self.max_workers)

        # Timing start
        start_time = datetime.now()
        self.last_run_start = start_time

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(self.process_warranty_batch, batch) for batch in tags_batches]

            for fut in concurrent.futures.as_completed(futures):
                try:
                    batch_result = fut.result()
                    if batch_result:
                        # agregação centralizada (apenas nesta thread)
                        self.results.extend(batch_result)
                except Exception as ex:
                    logging.exception('Future gerou exceção: %s', ex)

        end_time = datetime.now()
        self.last_run_end = end_time
        duration = end_time - start_time
        # store duration in seconds for programmatic access
        self.last_run_duration_seconds = duration.total_seconds()

        # human readable
        human = str(duration)
        logging.info('Processamento concluído. Total items agregados: %d', len(self.results))
        logging.info('Tempo total de execução: %s (%.2f segundos)', human, self.last_run_duration_seconds)

        return self.results


# --- utilitário exportável para ser usado pela rota do backend ---

def fetch_warranty_for_service_tags(servicetags, client_id=None, client_secret=None, *,
                                    max_workers=10, batch_size=100, request_delay=0.0, request_timeout=30.0, max_retries=2):
    """Convenience function para chamar o checker a partir do app Flask.

    Retorna a lista agregada de resultados (pode ser vazia em caso de erros).
    """
    checker = DellWarrantyChecker(
        servicetags_list=servicetags,
        client_id=client_id,
        client_secret=client_secret,
        max_workers=max_workers,
        batch_size=batch_size,
        request_delay=request_delay,
        request_timeout=request_timeout,
        max_retries=max_retries
    )

    return checker.run()


class DellWarrantyBulkUpdater:
    """
    Script para atualizar garantias Dell de todas as máquinas em massa
    """
    
    def __init__(self):
        self.connection_string = self._build_connection_string()
        self.dell_base_url = "https://apigtwb2c.us.dell.com"
        self.dell_token = None
        self.dell_token_expires_at = None
        self.token_lock = threading.Lock()
        
        # Estatísticas
        self.stats = {
            'total_computers': 0,
            'processed': 0,
            'success': 0,
            'errors': 0,
            'cached': 0,
            'api_calls': 0,
            'start_time': None,
            'end_time': None
        }
        
        # Configurações
        self.max_workers = 90  # Threads paralelas
        self.cache_duration_days = 7  # Cache válido por 7 dias
        self.retry_attempts = 3
        self.request_delay = 1  # Delay entre requests para não sobrecarregar API
        
        logger.info("DELL WARRANTY BULK UPDATER - Inicializado")
        logger.info(f"SQL Server: {SQL_SERVER}/{SQL_DATABASE}")
        logger.info(f"Configuracoes: {self.max_workers} threads, cache {self.cache_duration_days} dias")
        
        # Verificar e ajustar estrutura da tabela
        try:
            self.check_table_structure()
        except Exception as e:
            logger.error(f"ERRO: ao verificar estrutura da tabela: {e}")
            raise
    
    def _build_connection_string(self):
        """Constrói string de conexão SQL"""
        if USE_WINDOWS_AUTH:
            return f"""
                DRIVER={{ODBC Driver 17 for SQL Server}};
                SERVER={SQL_SERVER};
                DATABASE={SQL_DATABASE};
                Trusted_Connection=yes;
            """
        else:
            return f"""
                DRIVER={{ODBC Driver 17 for SQL Server}};
                SERVER={SQL_SERVER};
                DATABASE={SQL_DATABASE};
                UID={SQL_USERNAME};
                PWD={SQL_PASSWORD};
            """
    
    def get_connection(self):
        """Retorna nova conexão SQL"""
        return pyodbc.connect(self.connection_string)
    
    def get_dell_access_token(self):
        """Obtém token de acesso da API Dell com thread safety"""
        with self.token_lock:
            # Verificar se token ainda é válido
            if (self.dell_token and 
                self.dell_token_expires_at and 
                datetime.now() < self.dell_token_expires_at):
                return True
            
            try:
                url = f"{self.dell_base_url}/auth/oauth/v2/token"
                headers = {'Content-Type': 'application/x-www-form-urlencoded'}
                data = {
                    'grant_type': 'client_credentials',
                    'client_id': DELL_CLIENT_ID,
                    'client_secret': DELL_CLIENT_SECRET
                }
                
                logger.info("Renovando token Dell API...")
                response = requests.post(url, headers=headers, data=data, timeout=30)
                
                if response.status_code == 200:
                    token_data = response.json()
                    self.dell_token = token_data.get('access_token')
                    expires_in = token_data.get('expires_in', 3600)
                    self.dell_token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)
                    logger.info("Token Dell renovado com sucesso")
                    return True
                else:
                    logger.error(f"Erro na autenticacao Dell: {response.status_code}")
                    return False
                    
            except Exception as e:
                logger.error(f"Erro ao obter token Dell: {e}")
                return False
    
    def extract_service_tag_from_computer_name(self, computer_name):
        """Extrai service tag do nome da máquina"""
        name = computer_name.upper().strip()
        
        # Prefixos conhecidos
        prefixes = ['SHQ', 'ESM', 'DIA', 'TOP', 'RUB', 'JAD', 'ONI', 'CLO']
        
        for prefix in prefixes:
            if name.startswith(prefix):
                possible_service_tag = name[len(prefix):]
                # Se sobrou algo que parece service tag (letras e números, mínimo 5 chars)
                if possible_service_tag and len(possible_service_tag) >= 5:
                    return possible_service_tag
        
        # Se não tem prefixo, assumir que o nome todo é a service tag
        if len(name) >= 5:
            return name
        
        return None
    
    def get_computers_to_process(self):
        """Obtém lista de computadores para processar"""
        try:
            query = """
            SELECT 
                c.id,
                c.name,
                c.description,
                c.organization_id,
                o.name as organization_name,
                o.code as organization_code,
                dw.id as warranty_id,
                dw.last_updated,
                dw.cache_expires_at,
                dw.warranty_status,
                dw.last_error
            FROM computers c
            LEFT JOIN organizations o ON c.organization_id = o.id
            LEFT JOIN dell_warranty dw ON c.id = dw.computer_id
            WHERE c.is_domain_controller = 0
                AND c.name IS NOT NULL
                AND LEN(c.name) >= 5
            ORDER BY 
                CASE WHEN dw.cache_expires_at IS NULL OR dw.cache_expires_at < GETDATE() THEN 0 ELSE 1 END,
                c.name
            """
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                
                computers = []
                for row in cursor.fetchall():
                    # Extrair service tag do nome
                    service_tag = self.extract_service_tag_from_computer_name(row.name)
                    
                    if service_tag:
                        computers.append({
                            'id': row.id,
                            'name': row.name,
                            'service_tag': service_tag,
                            'description': row.description or '',
                            'organization_name': row.organization_name or '',
                            'organization_code': row.organization_code or '',
                            'warranty_id': row.warranty_id,
                            'last_updated': row.last_updated,
                            'cache_expires_at': row.cache_expires_at,
                            'warranty_status': row.warranty_status,
                            'last_error': row.last_error,
                            'needs_update': (
                                row.cache_expires_at is None or 
                                row.cache_expires_at < datetime.now() or
                                row.last_error is not None
                            )
                        })
                
                logger.info(f"Encontrados {len(computers)} computadores para processar")
                needs_update = sum(1 for c in computers if c['needs_update'])
                logger.info(f"{needs_update} precisam de atualizacao")
                
                return computers
                
        except Exception as e:
            logger.error(f"Erro ao buscar computadores: {e}")
            return []
    
    def get_warranty_from_dell_api(self, service_tag, original_name):
        """Busca garantia na API Dell"""
        try:
            if not self.get_dell_access_token():
                return {'error': 'Erro de autenticacao Dell API', 'code': 'AUTH_ERROR'}
            
            url = f"{self.dell_base_url}/PROD/sbil/eapi/v5/asset-entitlements"
            headers = {
                'Authorization': f'Bearer {self.dell_token}',
                'Accept': 'application/json'
            }
            params = {'servicetags': service_tag}
            
            # Delay para não sobrecarregar API
            time.sleep(self.request_delay)
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            self.stats['api_calls'] += 1
            
            if response.status_code == 200:
                data = response.json()
                
                if not data or len(data) == 0:
                    return {'error': 'Service tag nao encontrado', 'code': 'SERVICE_TAG_NOT_FOUND'}
                
                warranty_data = data[0]
                
                if warranty_data.get('invalid', False):
                    return {'error': 'Service tag invalido', 'code': 'INVALID_SERVICE_TAG'}
                
                # Processar entitlements para encontrar datas
                entitlements = warranty_data.get('entitlements', [])
                
                warranty_start_date = None
                warranty_end_date = None
                
                if entitlements:
                    start_dates = []
                    end_dates = []
                    
                    for ent in entitlements:
                        if ent.get('startDate'):
                            try:
                                start_date = datetime.fromisoformat(ent.get('startDate').replace('Z', '+00:00'))
                                start_dates.append(start_date)
                            except:
                                pass
                        
                        if ent.get('endDate'):
                            try:
                                end_date = datetime.fromisoformat(ent.get('endDate').replace('Z', '+00:00'))
                                end_dates.append(end_date)
                            except:
                                pass
                    
                    # Pegar a data de início mais antiga e fim mais recente
                    if start_dates:
                        warranty_start_date = min(start_dates)
                    
                    if end_dates:
                        warranty_end_date = max(end_dates)
                
                # Determinar status da garantia
                warranty_status = 'Unknown'
                if warranty_end_date:
                    now = datetime.now(timezone.utc)
                    if warranty_end_date.replace(tzinfo=timezone.utc) > now:
                        warranty_status = 'Active'
                    else:
                        warranty_status = 'Expired'
                elif entitlements:
                    warranty_status = 'Active'  # Assume ativo se tem entitlements mas sem data
                
                return {
                    'success': True,
                    'service_tag': service_tag,
                    'service_tag_clean': service_tag,
                    'warranty_start_date': warranty_start_date,
                    'warranty_end_date': warranty_end_date,
                    'warranty_status': warranty_status,
                    'product_line_description': warranty_data.get('productLineDescription', ''),
                    'system_description': warranty_data.get('systemDescription', ''),
                    'ship_date': warranty_data.get('shipDate'),
                    'order_number': warranty_data.get('orderNumber'),
                    'entitlements': json.dumps(entitlements, default=str),
                    'last_updated': datetime.now(),
                    'cache_expires_at': datetime.now() + timedelta(days=self.cache_duration_days),
                    'last_error': None
                }
                
            elif response.status_code == 401:
                # Token expirado, tentar renovar uma vez
                if self.get_dell_access_token():
                    return self.get_warranty_from_dell_api(service_tag, original_name)
                return {'error': 'Erro de autenticacao', 'code': 'AUTH_ERROR'}
                
            elif response.status_code == 404:
                return {'error': 'Service tag nao encontrado', 'code': 'SERVICE_TAG_NOT_FOUND'}
                
            else:
                return {'error': f'Erro API Dell (HTTP {response.status_code})', 'code': 'DELL_API_ERROR'}
                
        except requests.exceptions.Timeout:
            return {'error': 'Timeout na conexao com Dell API', 'code': 'TIMEOUT_ERROR'}
        except Exception as e:
            logger.error(f"Erro inesperado ao consultar Dell API para {service_tag}: {e}")
            return {'error': f'Erro interno: {str(e)}', 'code': 'INTERNAL_ERROR'}
    
    def check_table_structure(self):
        """Verifica e ajusta a estrutura da tabela dell_warranty"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Verificar se a tabela existe
                table_check = """
                SELECT COUNT(*) as table_exists
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = 'dell_warranty'
                """
                cursor.execute(table_check)
                table_exists = cursor.fetchone().table_exists
                
                if not table_exists:
                    logger.info("Tabela dell_warranty nao existe. Criando...")
                    self._create_dell_warranty_table(cursor)
                    conn.commit()
                    return
                
                # Verificar colunas existentes
                column_check = """
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = 'dell_warranty'
                """
                cursor.execute(column_check)
                existing_columns = [row.COLUMN_NAME.lower() for row in cursor.fetchall()]
                
                logger.info(f"Colunas existentes na tabela: {existing_columns}")
                
                # Colunas obrigatórias
                required_columns = {
                    'id': 'int IDENTITY(1,1) NOT NULL PRIMARY KEY',
                    'computer_id': 'int NOT NULL',
                    'service_tag': 'nvarchar(50) NULL',
                    'service_tag_clean': 'nvarchar(50) NULL',
                    'warranty_start_date': 'datetime2(7) NULL',
                    'warranty_end_date': 'datetime2(7) NULL',
                    'warranty_status': 'nvarchar(20) NULL',
                    'product_line_description': 'nvarchar(255) NULL',
                    'system_description': 'nvarchar(255) NULL',
                    'ship_date': 'datetime2(7) NULL',
                    'order_number': 'nvarchar(100) NULL',
                    'entitlements': 'ntext NULL',
                    'last_updated': 'datetime2(7) NULL',
                    'cache_expires_at': 'datetime2(7) NULL',
                    'last_error': 'nvarchar(500) NULL',
                    'created_at': 'datetime2(7) NULL DEFAULT (getdate())'
                }
                
                # Adicionar colunas que não existem
                for column_name, column_def in required_columns.items():
                    if column_name.lower() not in existing_columns:
                        if column_name == 'id':
                            continue  # ID deve ser criado com a tabela
                        
                        logger.info(f"Adicionando coluna {column_name}...")
                        alter_sql = f"ALTER TABLE dell_warranty ADD {column_name} {column_def}"
                        cursor.execute(alter_sql)
                
                conn.commit()
                logger.info("Estrutura da tabela verificada e ajustada")
                
        except Exception as e:
            logger.error(f"Erro ao verificar estrutura da tabela: {e}")
            raise
    
    def _create_dell_warranty_table(self, cursor):
        """Cria a tabela dell_warranty"""
        create_table_sql = """
        CREATE TABLE [dbo].[dell_warranty] (
            [id] [int] IDENTITY(1,1) NOT NULL,
            [computer_id] [int] NOT NULL,
            [service_tag] [nvarchar](50) NULL,
            [service_tag_clean] [nvarchar](50) NULL,
            [warranty_start_date] [datetime2](7) NULL,
            [warranty_end_date] [datetime2](7) NULL,
            [warranty_status] [nvarchar](20) NULL,
            [product_line_description] [nvarchar](255) NULL,
            [system_description] [nvarchar](255) NULL,
            [ship_date] [datetime2](7) NULL,
            [order_number] [nvarchar](100) NULL,
            [entitlements] [ntext] NULL,
            [last_updated] [datetime2](7) NULL,
            [cache_expires_at] [datetime2](7) NULL,
            [last_error] [nvarchar](500) NULL,
            [created_at] [datetime2](7) NULL DEFAULT (getdate()),
            CONSTRAINT [PK_dell_warranty] PRIMARY KEY CLUSTERED ([id] ASC)
        );
        
        CREATE UNIQUE INDEX [IX_dell_warranty_computer_id] ON [dbo].[dell_warranty] ([computer_id]);
        CREATE INDEX [IX_dell_warranty_status] ON [dbo].[dell_warranty] ([warranty_status]);
        CREATE INDEX [IX_dell_warranty_end_date] ON [dbo].[dell_warranty] ([warranty_end_date]);
        CREATE INDEX [IX_dell_warranty_cache_expires] ON [dbo].[dell_warranty] ([cache_expires_at]);
        """
        
        for statement in create_table_sql.split(';'):
            if statement.strip():
                cursor.execute(statement.strip())
    
    def save_warranty_to_database(self, computer_id, warranty_data):
        """Salva ou atualiza garantia no banco - versão compatível"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if warranty_data.get('success'):
                    # Verificar se já existe registro
                    check_query = "SELECT id FROM dell_warranty WHERE computer_id = ?"
                    cursor.execute(check_query, (computer_id,))
                    existing = cursor.fetchone()
                    
                    if existing:
                        # UPDATE
                        update_query = """
                        UPDATE dell_warranty SET
                            service_tag = ?,
                            service_tag_clean = ?,
                            warranty_start_date = ?,
                            warranty_end_date = ?,
                            warranty_status = ?,
                            product_line_description = ?,
                            system_description = ?,
                            ship_date = ?,
                            order_number = ?,
                            entitlements = ?,
                            last_updated = GETDATE(),
                            cache_expires_at = ?,
                            last_error = NULL
                        WHERE computer_id = ?
                        """
                        
                        params = (
                            warranty_data.get('service_tag'),
                            warranty_data.get('service_tag_clean'),
                            warranty_data.get('warranty_start_date'),
                            warranty_data.get('warranty_end_date'),
                            warranty_data.get('warranty_status'),
                            warranty_data.get('product_line_description'),
                            warranty_data.get('system_description'),
                            warranty_data.get('ship_date'),
                            warranty_data.get('order_number'),
                            warranty_data.get('entitlements'),
                            warranty_data.get('cache_expires_at'),
                            computer_id
                        )
                    else:
                        # INSERT
                        insert_query = """
                        INSERT INTO dell_warranty (
                            computer_id, service_tag, service_tag_clean, warranty_start_date, warranty_end_date,
                            warranty_status, product_line_description, system_description, ship_date, order_number,
                            entitlements, last_updated, cache_expires_at, last_error, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE(), ?, NULL, GETDATE())
                        """
                        
                        params = (
                            computer_id,
                            warranty_data.get('service_tag'),
                            warranty_data.get('service_tag_clean'),
                            warranty_data.get('warranty_start_date'),
                            warranty_data.get('warranty_end_date'),
                            warranty_data.get('warranty_status'),
                            warranty_data.get('product_line_description'),
                            warranty_data.get('system_description'),
                            warranty_data.get('ship_date'),
                            warranty_data.get('order_number'),
                            warranty_data.get('entitlements'),
                            warranty_data.get('cache_expires_at')
                        )
                        
                        update_query = insert_query
                else:
                    # Erro na consulta - verificar se existe e salvar só o erro
                    check_query = "SELECT id FROM dell_warranty WHERE computer_id = ?"
                    cursor.execute(check_query, (computer_id,))
                    existing = cursor.fetchone()
                    
                    if existing:
                        # UPDATE apenas campos de erro
                        update_query = """
                        UPDATE dell_warranty SET
                            last_updated = GETDATE(),
                            cache_expires_at = ?,
                            last_error = ?
                        WHERE computer_id = ?
                        """
                        
                        params = (
                            datetime.now() + timedelta(hours=6),  # Retry em 6 horas para erros
                            f"{warranty_data.get('code', 'ERROR')}: {warranty_data.get('error', 'Unknown error')}",
                            computer_id
                        )
                    else:
                        # INSERT apenas com erro
                        update_query = """
                        INSERT INTO dell_warranty (
                            computer_id, service_tag, last_updated, cache_expires_at, last_error, created_at
                        ) VALUES (?, ?, GETDATE(), ?, ?, GETDATE())
                        """
                        
                        params = (
                            computer_id,
                            warranty_data.get('service_tag', ''),
                            datetime.now() + timedelta(hours=6),
                            f"{warranty_data.get('code', 'ERROR')}: {warranty_data.get('error', 'Unknown error')}"
                        )
                
                cursor.execute(update_query, params)
                conn.commit()
                
                return True
                
        except Exception as e:
            logger.error(f"Erro ao salvar garantia no banco para computer_id {computer_id}: {e}")
            return False
    
    def process_computer_warranty(self, computer):
        """Processa garantia de um computador específico"""
        computer_id = computer['id']
        computer_name = computer['name']
        service_tag = computer['service_tag']
        
        try:
            # Verificar se precisa atualizar
            if not computer['needs_update']:
                logger.debug(f"CACHE: {computer_name} ({service_tag}) - Cache valido, pulando")
                self.stats['cached'] += 1
                return {'status': 'cached', 'computer_name': computer_name}
            
            logger.info(f"PROCESSANDO: {computer_name} ({service_tag})...")
            
            # Buscar garantia na Dell API
            warranty_data = self.get_warranty_from_dell_api(service_tag, computer_name)
            
            # Salvar no banco
            saved = self.save_warranty_to_database(computer_id, warranty_data)
            
            if warranty_data.get('success') and saved:
                status = warranty_data.get('warranty_status', 'Unknown')
                end_date = warranty_data.get('warranty_end_date')
                end_date_str = end_date.strftime('%d/%m/%Y') if end_date else 'N/A'
                
                logger.info(f"SUCESSO: {computer_name} - Status: {status}, Expira: {end_date_str}")
                self.stats['success'] += 1
                return {
                    'status': 'success', 
                    'computer_name': computer_name,
                    'warranty_status': status,
                    'warranty_end_date': end_date_str
                }
            else:
                error_msg = warranty_data.get('error', 'Erro desconhecido')
                logger.warning(f"AVISO: {computer_name} - Erro: {error_msg}")
                self.stats['errors'] += 1
                return {
                    'status': 'error', 
                    'computer_name': computer_name,
                    'error': error_msg
                }
                
        except Exception as e:
            logger.error(f"ERRO: ao processar {computer_name}: {e}")
            self.stats['errors'] += 1
            return {
                'status': 'exception', 
                'computer_name': computer_name,
                'error': str(e)
            }
        finally:
            self.stats['processed'] += 1
    
    def run_bulk_update(self, max_computers=None, only_expired=False, only_errors=False):
        """Executa atualização em massa"""
        logger.info("INICIANDO: atualizacao em massa das garantias Dell")
        self.stats['start_time'] = datetime.now()
        
        try:
            # Buscar computadores para processar
            computers = self.get_computers_to_process()
            
            if not computers:
                logger.warning("AVISO: Nenhum computador encontrado para processar")
                return
            
            # Aplicar filtros
            if only_expired:
                computers = [c for c in computers if c.get('warranty_status') == 'Expired']
                logger.info(f"FILTRO: apenas garantias expiradas ({len(computers)} computadores)")
            
            if only_errors:
                computers = [c for c in computers if c.get('last_error')]
                logger.info(f"FILTRO: apenas com erros anteriores ({len(computers)} computadores)")
            
            # Limitar quantidade se especificado
            if max_computers and max_computers > 0:
                computers = computers[:max_computers]
                logger.info(f"LIMITE: processamento limitado a {max_computers} computadores")
            
            self.stats['total_computers'] = len(computers)
            
            if not computers:
                logger.warning("AVISO: Nenhum computador restou apos aplicar filtros")
                return
            
            logger.info(f"PROCESSANDO: {len(computers)} computadores com {self.max_workers} threads")
            
            # Processar em paralelo
            results = {'success': [], 'errors': [], 'cached': []}
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submeter tarefas
                future_to_computer = {
                    executor.submit(self.process_computer_warranty, computer): computer 
                    for computer in computers
                }
                
                # Processar resultados conforme completam
                for future in as_completed(future_to_computer):
                    computer = future_to_computer[future]
                    try:
                        result = future.result()
                        
                        if result['status'] == 'success':
                            results['success'].append(result)
                        elif result['status'] == 'cached':
                            results['cached'].append(result)
                        else:
                            results['errors'].append(result)
                        
                        # Log de progresso a cada 10 computadores
                        if self.stats['processed'] % 10 == 0:
                            progress = (self.stats['processed'] / self.stats['total_computers']) * 100
                            logger.info(f"PROGRESSO: {self.stats['processed']}/{self.stats['total_computers']} ({progress:.1f}%)")
                            
                    except Exception as e:
                        logger.error(f"ERRO: no future para {computer['name']}: {e}")
                        self.stats['errors'] += 1
                        results['errors'].append({
                            'status': 'exception',
                            'computer_name': computer['name'],
                            'error': str(e)
                        })
            
            self.stats['end_time'] = datetime.now()
            self._print_final_report(results)
            
        except Exception as e:
            logger.error(f"ERRO GERAL: na atualizacao em massa: {e}")
            raise
    
    def _print_final_report(self, results):
        """Imprime relatório final"""
        duration = self.stats['end_time'] - self.stats['start_time']
        
        logger.info("=" * 80)
        logger.info("RELATORIO FINAL DA ATUALIZACAO EM MASSA")
        logger.info("=" * 80)
        logger.info(f"Tempo total: {duration}")
        logger.info(f"Total de computadores: {self.stats['total_computers']}")
        logger.info(f"Sucessos: {self.stats['success']}")
        logger.info(f"Erros: {self.stats['errors']}")
        logger.info(f"Cache (nao atualizados): {self.stats['cached']}")
        logger.info(f"Chamadas API Dell: {self.stats['api_calls']}")
        
        if self.stats['total_computers'] > 0:
            success_rate = (self.stats['success'] / self.stats['total_computers']) * 100
            logger.info(f"Taxa de sucesso: {success_rate:.1f}%")
        
        # Mostrar alguns erros se houver
        if results['errors']:
            logger.info("AMOSTRA DE ERROS:")
            for error in results['errors'][:5]:  # Mostrar apenas os primeiros 5
                logger.info(f"   - {error['computer_name']}: {error.get('error', 'Erro desconhecido')}")
            
            if len(results['errors']) > 5:
                logger.info(f"   ... e mais {len(results['errors']) - 5} erros")
        
        logger.info("=" * 80)
    
    def get_warranty_summary_report(self):
        """Gera relatório resumo das garantias"""
        try:
            query = """
            SELECT 
                warranty_status,
                COUNT(*) as count,
                COUNT(*) * 100.0 / SUM(COUNT(*)) OVER() as percentage
            FROM dell_warranty dw
            INNER JOIN computers c ON dw.computer_id = c.id
            WHERE c.is_domain_controller = 0
                AND dw.last_error IS NULL
            GROUP BY warranty_status
            ORDER BY count DESC
            """
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                
                logger.info("")
                logger.info("RELATORIO RESUMO DAS GARANTIAS:")
                logger.info("-" * 50)
                
                for row in cursor.fetchall():
                    status = row.warranty_status or 'Desconhecido'
                    count = row.count
                    percentage = row.percentage
                    logger.info(f"{status:15}: {count:4d} ({percentage:5.1f}%)")
                
                # Garantias expirando em 30 dias
                expiring_query = """
                SELECT COUNT(*) as count
                FROM dell_warranty dw
                INNER JOIN computers c ON dw.computer_id = c.id
                WHERE c.is_domain_controller = 0
                    AND dw.warranty_end_date BETWEEN GETDATE() AND DATEADD(day, 30, GETDATE())
                    AND dw.warranty_status = 'Active'
                """
                
                cursor.execute(expiring_query)
                expiring_count = cursor.fetchone().count
                
                logger.info("-" * 50)
                logger.info(f"EXPIRANDO em 30 dias: {expiring_count}")
                
        except Exception as e:
            logger.error(f"Erro ao gerar relatorio: {e}")


def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Atualizacao em massa das garantias Dell')
    parser.add_argument('--max-computers', type=int, help='Maximo de computadores para processar')
    parser.add_argument('--only-expired', action='store_true', help='Processar apenas garantias expiradas')
    parser.add_argument('--only-errors', action='store_true', help='Processar apenas computadores com erros anteriores')
    parser.add_argument('--workers', type=int, default=5, help='Numero de threads paralelas (padrao: 5)')
    parser.add_argument('--report-only', action='store_true', help='Apenas gerar relatorio, sem atualizar')
    parser.add_argument('--cache-days', type=int, default=7, help='Dias para cache de garantias (padrao: 7)')
    parser.add_argument('--create-table', action='store_true', help='Criar tabela dell_warranty se nao existir')
    
    args = parser.parse_args()
    
    try:
        logger.info("=" * 60)
        logger.info("DELL WARRANTY BULK UPDATER - INICIANDO")
        logger.info("=" * 60)
        
        updater = DellWarrantyBulkUpdater()
        updater.max_workers = args.workers
        updater.cache_duration_days = args.cache_days
        
        if args.create_table:
            logger.info("Verificando/criando estrutura da tabela...")
            updater.check_table_structure()
            logger.info("Estrutura da tabela verificada com sucesso!")
            return
        
        if args.report_only:
            logger.info("Gerando apenas relatorio...")
            updater.get_warranty_summary_report()
        else:
            updater.run_bulk_update(
                max_computers=args.max_computers,
                only_expired=args.only_expired,
                only_errors=args.only_errors
            )
            
            # Gerar relatório final
            updater.get_warranty_summary_report()
            
    except KeyboardInterrupt:
        logger.info("INTERROMPIDO pelo usuario")
        sys.exit(1)
    except Exception as e:
        logger.error(f"ERRO FATAL: {e}")
        import traceback
        logger.error(f"TRACEBACK: {traceback.format_exc()}")
        sys.exit(1)


if __name__ == "__main__":
    main()