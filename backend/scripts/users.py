#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para buscar usuários logados em máquinas SHQ e atualizar no banco de dados
"""

import os
import sys
import time
import pyodbc
import logging
import argparse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
import subprocess
import re
from pathlib import Path

# Adicionar o diretório backend ao path para importar módulos da API
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

# Carregar variáveis de ambiente
load_dotenv(dotenv_path=backend_dir / '.env')

# Importar configurações da API principal
try:
    from fastapi_app.config import SQL_SERVER, SQL_DATABASE, SQL_USERNAME, SQL_PASSWORD, USE_WINDOWS_AUTH
except ImportError:
    # Fallback para valores padrão se não conseguir importar
    SQL_SERVER = os.getenv('SQL_SERVER', 'CLOSQL02')
    SQL_DATABASE = os.getenv('SQL_DATABASE', 'DellReports')
    SQL_USERNAME = os.getenv('SQL_USERNAME')
    SQL_PASSWORD = os.getenv('SQL_PASSWORD')
    USE_WINDOWS_AUTH = os.getenv('USE_WINDOWS_AUTH', 'true').lower() == 'true'

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('users_update.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

class SQLManager:
    def __init__(self):
        self.connection_string = self._build_connection_string()
        self._test_connection()
    
    def _build_connection_string(self):
        """Constrói string de conexão para SQL Server usando as mesmas configurações da API"""
        try:
            if USE_WINDOWS_AUTH:
                connection_string = f"""
                    DRIVER={{SQL Server}};
                    SERVER={SQL_SERVER};
                    DATABASE={SQL_DATABASE};
                    Trusted_Connection=yes;
                """
            else:
                connection_string = f"""
                    DRIVER={{SQL Server}};
                    SERVER={SQL_SERVER};
                    DATABASE={SQL_DATABASE};
                    UID={SQL_USERNAME};
                    PWD={SQL_PASSWORD};
                """
            
            logger.info(f"[CONFIG] Conectando ao SQL Server: {SQL_SERVER}/{SQL_DATABASE}")
            logger.info(f"[CONFIG] Usando Windows Auth: {USE_WINDOWS_AUTH}")
            return connection_string
            
        except Exception as e:
            logger.error(f"[CONFIG] Erro ao construir string de conexão: {e}")
            raise
    
    def _test_connection(self):
        """Testa conexão com SQL Server"""
        try:
            with pyodbc.connect(self.connection_string) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                logger.info("[OK] Conexao SQL Server estabelecida")
        except Exception as e:
            logger.error(f"[ERRO] Erro na conexao SQL Server: {e}")
            raise
    
    def get_connection(self):
        """Retorna nova conexão SQL"""
        return pyodbc.connect(self.connection_string)
    
    def execute_query(self, query, params=None, fetch=True):
        """Executa query SQL"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                if fetch:
                    columns = [column[0] for column in cursor.description] if cursor.description else []
                    rows = cursor.fetchall()
                    return [dict(zip(columns, row)) for row in rows]
                else:
                    conn.commit()
                    return cursor.rowcount
                    
        except Exception as e:
            logger.error(f"[ERRO] Erro SQL: {e}")
            raise

class UserManager:
    def __init__(self):
        self.sql_manager = SQLManager()
        self.ad_username = os.getenv('AD_USERNAME', 'SNM\\adm.itservices')
        self.ad_password = os.getenv('AD_PASSWORD', 'xmZ7P@5vkKzg')
        
    def get_shq_computers(self, limit=20, specific_machine=None):
        """Busca máquinas SHQ do banco de dados"""
        if specific_machine:
            # Busca máquina específica
            query = """
            SELECT 
                id,
                name,
                dns_hostname,
                is_enabled,
                Usuario_Atual
            FROM computers 
            WHERE name = ?
                AND is_enabled = 1
                AND is_domain_controller = 0
            """
            params = (specific_machine,)
            logger.info(f"[INFO] Buscando maquina especifica: {specific_machine}")
        else:
            # Busca máquinas SHQ com limite
            query = """
            SELECT TOP (?) 
                id,
                name,
                dns_hostname,
                is_enabled,
                Usuario_Atual
            FROM computers 
            WHERE name LIKE 'SHQ%' 
                AND is_enabled = 1
                AND is_domain_controller = 0
            ORDER BY name
            """
            params = (limit,)
            logger.info(f"[INFO] Buscando {limit} maquinas SHQ")
        
        try:
            results = self.sql_manager.execute_query(query, params)
            logger.info(f"[INFO] Encontradas {len(results)} maquinas")
            return results
        except Exception as e:
            logger.error(f"[ERRO] Erro ao buscar maquinas: {e}")
            return []
    
    def get_logged_user_remote(self, computer_name, timeout=30):
        """Busca usuário logado remotamente via PowerShell.

        Retorna uma tupla: (username_or_None, error_message_or_None).
        """
        try:
            # Script PowerShell para buscar usuário logado remotamente
            ps_script = f"""
            try {{
                $user = (Get-CimInstance Win32_ComputerSystem -ComputerName {computer_name} -ErrorAction Stop).UserName
                if ($user) {{
                    Write-Output $user
                }} else {{
                    Write-Output "NENHUM_USUARIO"
                }}
            }} catch {{
                Write-Output "ERRO_CONEXAO: $($_.Exception.Message)"
            }}
            """

            # Executa PowerShell
            result = subprocess.run([
                'powershell.exe',
                '-Command',
                ps_script
            ],
                capture_output=True,
                text=True,
                timeout=timeout
            )

            if result.returncode != 0:
                errmsg = result.stderr.strip() or f"returncode={result.returncode}"
                logger.warning(f"[WARN] PowerShell falhou para {computer_name}: {errmsg}")
                return (None, errmsg)

            output = result.stdout.strip()

            if output and not output.startswith("NENHUM_USUARIO") and not output.startswith("ERRO_CONEXAO"):
                return (output, None)
            else:
                # Retorna mensagem de erro para que possamos decidir fallback (PsExec)
                logger.info(f"[INFO] Nenhum usuario logado em {computer_name}: {output}")
                return (None, output)

        except subprocess.TimeoutExpired:
            logger.warning(f"[WARN] Timeout ao conectar em {computer_name}")
            return (None, 'TIMEOUT')
        except Exception as e:
            logger.warning(f"[WARN] Nao foi possivel conectar em {computer_name}: {str(e)}")
            return (None, str(e))

    def run_psexec_activate(self, computer_name, timeout=10):
        """Tenta executar PsExec para rodar 'winrm quickconfig -q' remotamente usando credenciais configuradas.

        Retorna tuple (success: bool, output: str).
        """
        # Procura PsExec em 3 locais (prioridade):
        # 1) variável de ambiente PSEXEC_PATH
        # 2) pasta `psexec` no repositório
        # 3) caminho hardcoded antigo (fallback)
        psexec_env = os.getenv('PSEXEC_PATH')
        # Caminho correto para a pasta psexec na raiz do repositório
        repo_default = str(Path(__file__).resolve().parents[3] / 'psexec' / 'PsExec.exe')
        hardcoded = r'C:\Users\adm.itservices\Downloads\PSTools\PsExec.exe'

        psexec_path = psexec_env or repo_default or hardcoded
        logger.info(f"[INFO] Usando PsExec em: {psexec_path}")

        username = self.ad_username
        password = os.getenv('AD_PASSWORD', None)

        # Se não existir o executável
        if not os.path.exists(psexec_path):
            logger.error(f"[ERROR] PsExec nao encontrado em: {psexec_path}")
            return (False, 'PSEXEC_NOT_FOUND')
        target = f"\\\\{computer_name}"

        # Se estiver configurado para usar Windows Auth e não houver senha,
        # tenta executar PsExec sem -u/-p (usa credenciais do usuário atual)
        if USE_WINDOWS_AUTH and not password:
            logger.info(f"[INFO] USE_WINDOWS_AUTH ativo e sem AD_PASSWORD: tentando PsExec com usuario Windows atual para {computer_name}")
            args = [
                psexec_path,
                target,
                '-accepteula',
                '-s',
                'cmd.exe',
                '/c',
                'winrm quickconfig -q'
            ]
        else:
            if not password:
                logger.error(f"[ERROR] PSExec requerido, mas variavel AD_PASSWORD nao configurada para {computer_name}")
                return (False, 'NO_PASSWORD')

            args = [
                psexec_path,
                target,
                '-accepteula',
                '-h',
                '-u', username,
                '-p', password,
                '-s',
                'cmd.exe',
                '/c',
                'winrm quickconfig -q'
            ]

        try:
            logger.info(f"[INFO] Tentando PsExec->winrm quickconfig em {computer_name} com {username} (timeout={timeout}s)")
            proc = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
            output = (proc.stdout or '') + '\n' + (proc.stderr or '')
            rc = proc.returncode
            if rc == 0:
                logger.info(f"[INFO] PsExec executado (rc=0) em {computer_name}")
                return (True, output)
            else:
                logger.warning(f"[WARN] PsExec rc={rc} em {computer_name}: {output}")
                return (False, output)
        except subprocess.TimeoutExpired:
            logger.warning(f"[WARN] PsExec timeout em {computer_name} (>{timeout}s)")
            return (False, 'PSEXEC_TIMEOUT')
        except Exception as e:
            logger.error(f"[ERROR] Erro ao executar PsExec em {computer_name}: {e}")
            return (False, str(e))
    
    def format_username(self, domain_user):
        """Converte SNM\\philipe.fernandes para Philipe Fernandes"""
        if not domain_user or '\\' not in domain_user:
            return domain_user
        
        try:
            # Remove o domínio
            username = domain_user.split('\\')[1]
            
            # Remove pontos e converte para nome próprio
            name_parts = username.replace('.', ' ').split()
            formatted_name = ' '.join([part.capitalize() for part in name_parts])
            
            return formatted_name
        except Exception as e:
            logger.warning(f"[WARN] Erro ao formatar usuario {domain_user}: {e}")
            return domain_user
    
    def update_computer_user(self, computer_id, formatted_user):
        """Atualiza usuário no banco de dados"""
        try:
            # Verifica se existe coluna current_user na tabela computers
            query_check = """
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'computers' 
                AND COLUMN_NAME = 'Usuario_Atual'
            """
            
            result = self.sql_manager.execute_query(query_check)
            
            if not result:
                # Cria a coluna se não existir
                logger.info("[INFO] Criando coluna current_user na tabela computers...")
                alter_query = "ALTER TABLE computers ADD current_user NVARCHAR(255)"
                self.sql_manager.execute_query(alter_query, fetch=False)
                logger.info("[OK] Coluna current_user criada")
            
            # Atualiza o usuário na coluna Usuario_Atual que já existe
            update_query = """
            UPDATE computers 
            SET Usuario_Atual = ?, 
                updated_at = GETDATE()
            WHERE id = ?
            """
            
            rows_affected = self.sql_manager.execute_query(
                update_query, 
                (formatted_user, computer_id), 
                fetch=False
            )
            
            return rows_affected > 0
            
        except Exception as e:
            logger.error(f"[ERRO] Erro ao atualizar usuario no banco: {e}")
            return False
    
    def process_computer(self, computer):
        """Processa uma máquina individualmente"""
        computer_name = computer['name']
        computer_id = computer['id']
        
        logger.info(f"[PROCESS] Processando {computer_name}...")
        
        start_time = time.time()
        
        # Busca usuário logado (retorna (user, error))
        domain_user, error = self.get_logged_user_remote(computer_name)

        # Se não obteve usuário e erro sugere que WinRM/remote está desativado, tenta PsExec com credenciais
        if not domain_user:
            should_attempt_psexec = False
            if error:
                err_up = str(error).upper()
                # Frases/flags que indicam provável falta de WinRM/remote
                indicators = ['ERRO_CONEXAO', 'WINRM', 'WSMAN', 'TIMEOUT', 'RPC', 'COULD NOT', 'ACCESS', 'NEGOTIATE']
                if any(ind in err_up for ind in indicators):
                    should_attempt_psexec = True

            if should_attempt_psexec:
                # Tenta ativar WinRM via PsExec e re-tentar
                ok, psexec_out = self.run_psexec_activate(computer_name, timeout=10)
                if ok:
                    # Aguarda curto tempo e tenta buscar usuário novamente com timeout reduzido
                    time.sleep(2)
                    domain_user, error = self.get_logged_user_remote(computer_name, timeout=10)

        if domain_user:
            # Formata o nome do usuário
            formatted_user = self.format_username(domain_user)

            # Atualiza no banco
            success = self.update_computer_user(computer_id, formatted_user)

            elapsed = time.time() - start_time

            if success:
                logger.info(f"[SUCCESS] {computer_name}: {domain_user} -> {formatted_user} ({elapsed:.1f}s)")
                return {
                    'computer': computer_name,
                    'success': True,
                    'domain_user': domain_user,
                    'formatted_user': formatted_user,
                    'elapsed': elapsed
                }
            else:
                logger.error(f"[ERRO] {computer_name}: Falha ao atualizar no banco")
                return {
                    'computer': computer_name,
                    'success': False,
                    'error': 'Falha ao atualizar no banco',
                    'elapsed': elapsed
                }
        else:
            elapsed = time.time() - start_time
            logger.warning(f"[WARN] {computer_name}: Usuario nao encontrado ({elapsed:.1f}s) - erro: {error}")
            return {
                'computer': computer_name,
                'success': False,
                'error': 'Usuario nao encontrado',
                'detail': error,
                'elapsed': elapsed
            }
    
    def run_user_update(self, limit=20, max_workers=5, specific_machine=None):
        """Executa atualização de usuários para máquinas SHQ"""
        if specific_machine:
            logger.info(f"[START] Iniciando atualizacao de usuario para maquina: {specific_machine}")
        else:
            logger.info(f"[START] Iniciando atualizacao de usuarios para {limit} maquinas SHQ...")
        
        start_time = time.time()
        
        # Busca máquinas
        computers = self.get_shq_computers(limit, specific_machine)
        
        if not computers:
            if specific_machine:
                logger.warning(f"[WARN] Maquina {specific_machine} nao encontrada")
            else:
                logger.warning("[WARN] Nenhuma maquina SHQ encontrada")
            return
        
        results = []
        success_count = 0
        
        # Processa máquinas em paralelo (limitado)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_computer = {
                executor.submit(self.process_computer, computer): computer 
                for computer in computers
            }
            
            for future in as_completed(future_to_computer):
                result = future.result()
                results.append(result)
                
                if result['success']:
                    success_count += 1
        
        total_time = time.time() - start_time
        
        # Relatório final
        logger.info("=" * 60)
        logger.info(f"[REPORT] RELATORIO FINAL")
        logger.info(f"Total de maquinas: {len(computers)}")
        logger.info(f"Sucessos: {success_count}")
        logger.info(f"Falhas: {len(computers) - success_count}")
        logger.info(f"Tempo total: {total_time:.1f}s")
        logger.info(f"Tempo medio por maquina: {total_time/len(computers):.1f}s")
        logger.info("=" * 60)
        
        # Log detalhado dos resultados
        for result in results:
            if result['success']:
                logger.info(f"[OK] {result['computer']}: {result['formatted_user']}")
            else:
                logger.warning(f"[FAIL] {result['computer']}: {result['error']}")

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description='Atualiza usuarios logados em maquinas SHQ')
    parser.add_argument('-m', '--machine', 
                       help='Nome da maquina especifica para processar (ex: SHQ001)')
    parser.add_argument('-l', '--limit', 
                       type=int, 
                       default=20,
                       help='Numero maximo de maquinas SHQ para processar (padrao: 20)')
    parser.add_argument('-w', '--workers', 
                       type=int, 
                       default=3,
                       help='Numero de threads paralelas (padrao: 3)')
    
    args = parser.parse_args()
    
    try:
        user_manager = UserManager()
        user_manager.run_user_update(
            limit=args.limit, 
            max_workers=args.workers,
            specific_machine=args.machine
        )
        
    except KeyboardInterrupt:
        logger.info("[STOP] Processo interrompido pelo usuario")
    except Exception as e:
        logger.error(f"[CRITICAL] Erro critico: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
