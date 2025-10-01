"""
Integração com SQL Server para consultas do Active Directory
"""

import logging
from typing import List, Dict, Any, Optional
from contextlib import contextmanager
import time

try:
    import pyodbc
    SQL_SERVER_AVAILABLE = True
except ImportError:
    SQL_SERVER_AVAILABLE = False
    pyodbc = None

from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class SQLServerManager:
    """Gerenciador de conexões com SQL Server para consultas AD"""
    
    def __init__(self):
        self.connection_string = None
        self.is_available = SQL_SERVER_AVAILABLE
        
        if not self.is_available:
            logger.warning("⚠️ pyodbc não disponível. Instale com: pip install pyodbc")
            return
        
        # Construir connection string se as configurações estão disponíveis
        if all([settings.SQL_SERVER_HOST, settings.SQL_SERVER_DATABASE, 
               settings.SQL_SERVER_USERNAME, settings.SQL_SERVER_PASSWORD]):
            
            self.connection_string = (
                f"DRIVER={{{settings.SQL_SERVER_DRIVER}}};"
                f"SERVER={settings.SQL_SERVER_HOST};"
                f"DATABASE={settings.SQL_SERVER_DATABASE};"
                f"UID={settings.SQL_SERVER_USERNAME};"
                f"PWD={settings.SQL_SERVER_PASSWORD};"
                f"TrustServerCertificate=yes;"
                f"Encrypt=yes;"
            )
            logger.info(f"🔗 SQL Server configurado: {settings.SQL_SERVER_HOST}")
        else:
            logger.warning("⚠️ Configurações do SQL Server incompletas")
            self.is_available = False

    @contextmanager
    def get_connection(self):
        """Context manager para conexões SQL Server"""
        if not self.is_available or not self.connection_string:
            raise Exception("SQL Server não está disponível ou configurado")
        
        conn = None
        try:
            conn = pyodbc.connect(self.connection_string, timeout=30)
            conn.autocommit = True
            yield conn
        except pyodbc.Error as e:
            logger.error(f"❌ Erro de conexão SQL Server: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def test_connection(self) -> Dict[str, Any]:
        """Testa a conexão com SQL Server"""
        if not self.is_available:
            return {'success': False, 'error': 'pyodbc não disponível'}
        
        if not self.connection_string:
            return {'success': False, 'error': 'SQL Server não configurado'}
        
        try:
            start_time = time.time()
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 as test, @@VERSION as version")
                result = cursor.fetchone()
                
                response_time = round((time.time() - start_time) * 1000, 2)
                
                return {
                    'success': True,
                    'version': result.version if result else 'Unknown',
                    'response_time_ms': response_time,
                    'server': settings.SQL_SERVER_HOST,
                    'database': settings.SQL_SERVER_DATABASE
                }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Executa query no SQL Server e retorna resultados"""
        if not self.is_available:
            raise Exception("SQL Server não disponível")
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                # Obter nomes das colunas
                columns = [column[0] for column in cursor.description] if cursor.description else []
                
                # Obter dados
                rows = cursor.fetchall()
                
                # Converter para lista de dicionários
                results = []
                for row in rows:
                    row_dict = {}
                    for i, value in enumerate(row):
                        if i < len(columns):
                            # Converter datetime para string se necessário
                            if hasattr(value, 'isoformat'):
                                value = value.isoformat()
                            row_dict[columns[i]] = value
                    results.append(row_dict)
                
                return results
                
        except Exception as e:
            logger.error(f"❌ Erro ao executar query SQL Server: {e}")
            raise

    def get_ad_computers(self, limit: int = None) -> List[Dict[str, Any]]:
        """
        Busca computadores do Active Directory via SQL Server
        
        Esta query assume que você tem uma view ou tabela no SQL Server
        que sincroniza com o AD. Ajuste conforme sua infraestrutura.
        """
        if not self.is_available:
            return []
        
        try:
            # Query exemplo - ajustar conforme sua estrutura
            query = """
                SELECT 
                    name,
                    operatingSystem as os,
                    operatingSystemVersion as os_version,
                    description,
                    dNSHostName as dns_hostname,
                    distinguishedName as distinguished_name,
                    lastLogonTimestamp as last_logon,
                    whenCreated as created_date,
                    userAccountControl as user_account_control,
                    primaryGroupID as primary_group_id,
                    CASE WHEN userAccountControl & 2 = 2 THEN 1 ELSE 0 END as disabled
                FROM AD_Computers
                WHERE objectClass = 'computer'
                AND name IS NOT NULL
            """
            
            if limit:
                query += f" ORDER BY name OFFSET 0 ROWS FETCH NEXT {limit} ROWS ONLY"
            else:
                query += " ORDER BY name"
            
            results = self.execute_query(query)
            logger.info(f"📊 Carregados {len(results)} computadores do AD via SQL Server")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar computadores do AD: {e}")
            return []

    def get_ad_computer_by_name(self, computer_name: str) -> Optional[Dict[str, Any]]:
        """Busca um computador específico do AD"""
        if not self.is_available:
            return None
        
        try:
            query = """
                SELECT 
                    name,
                    operatingSystem as os,
                    operatingSystemVersion as os_version,
                    description,
                    dNSHostName as dns_hostname,
                    distinguishedName as distinguished_name,
                    lastLogonTimestamp as last_logon,
                    whenCreated as created_date,
                    userAccountControl as user_account_control,
                    primaryGroupID as primary_group_id,
                    CASE WHEN userAccountControl & 2 = 2 THEN 1 ELSE 0 END as disabled
                FROM AD_Computers
                WHERE UPPER(name) = UPPER(?)
                AND objectClass = 'computer'
            """
            
            results = self.execute_query(query, (computer_name,))
            return results[0] if results else None
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar computador {computer_name} do AD: {e}")
            return None

    def sync_computers_from_ad(self, batch_size: int = 1000) -> Dict[str, Any]:
        """
        Sincroniza computadores do AD para o banco SQLite local
        Processa em lotes para melhor performance
        """
        from app.config.database import get_database_manager
        
        if not self.is_available:
            return {'success': False, 'error': 'SQL Server não disponível'}
        
        try:
            db = get_database_manager()
            
            # Marcar todos como não sincronizados
            db.mark_all_computers_as_not_synced()
            
            # Buscar total de computadores
            count_query = "SELECT COUNT(*) as total FROM AD_Computers WHERE objectClass = 'computer' AND name IS NOT NULL"
            count_result = self.execute_query(count_query)
            total_computers = count_result[0]['total'] if count_result else 0
            
            logger.info(f"🔄 Iniciando sincronização de {total_computers} computadores do AD...")
            
            # Processar em lotes
            processed = 0
            offset = 0
            
            while offset < total_computers:
                # Query com paginação
                batch_query = """
                    SELECT 
                        name,
                        operatingSystem as os,
                        operatingSystemVersion as os_version,
                        description,
                        dNSHostName as dns_hostname,
                        distinguishedName as distinguished_name,
                        lastLogonTimestamp as last_logon,
                        whenCreated as created_date,
                        userAccountControl as user_account_control,
                        primaryGroupID as primary_group_id,
                        CASE WHEN userAccountControl & 2 = 2 THEN 1 ELSE 0 END as disabled
                    FROM AD_Computers
                    WHERE objectClass = 'computer' AND name IS NOT NULL
                    ORDER BY name
                    OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
                """
                
                batch_computers = self.execute_query(batch_query, (offset, batch_size))
                
                if not batch_computers:
                    break
                
                # Preparar dados para inserção
                computers_to_insert = []
                for computer in batch_computers:
                    computers_to_insert.append({
                        'name': computer['name'],
                        'os': computer.get('os'),
                        'os_version': computer.get('os_version'),
                        'description': computer.get('description'),
                        'dns_hostname': computer.get('dns_hostname'),
                        'distinguished_name': computer.get('distinguished_name'),
                        'last_logon': computer.get('last_logon'),
                        'created_date': computer.get('created_date'),
                        'user_account_control': computer.get('user_account_control'),
                        'primary_group_id': computer.get('primary_group_id'),
                        'disabled': computer.get('disabled', False),
                        'data_source': 'ad_sql_server',
                        'synced_from_ad': True
                    })
                
                # Inserir lote
                inserted = db.bulk_insert_computers(computers_to_insert)
                processed += len(batch_computers)
                offset += batch_size
                
                logger.info(f"📦 Processado lote: {processed}/{total_computers}")
            
            # Remover computadores que não existem mais no AD
            deleted = db.delete_non_synced_computers()
            
            # Estatísticas finais
            final_stats = db.get_computers_stats()
            
            result = {
                'success': True,
                'total_in_ad': total_computers,
                'computers_processed': processed,
                'computers_deleted': deleted,
                'computers_after_sync': final_stats.get('total', 0),
                'sync_time': time.time()
            }
            
            logger.info(f"✅ Sincronização AD concluída: {result}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro na sincronização AD: {e}")
            return {'success': False, 'error': str(e)}

    def get_computer_last_user_events(self, computer_name: str, days: int = 30) -> Optional[Dict[str, Any]]:
        """
        Busca eventos de logon do último usuário
        
        Esta função assume que você tem uma tabela de eventos do Windows
        no SQL Server. Ajuste conforme sua infraestrutura.
        """
        if not self.is_available:
            return None
        
        try:
            # Query exemplo para eventos de logon - ajustar conforme sua estrutura
            query = """
                SELECT TOP 5
                    ComputerName,
                    UserName,
                    EventDateTime,
                    LogonType,
                    SourceIP,
                    LogonProcess
                FROM WindowsEvents 
                WHERE EventID IN (4624, 4625)  -- Logon success/failure
                AND ComputerName = ?
                AND EventDateTime >= DATEADD(day, -?, GETDATE())
                ORDER BY EventDateTime DESC
            """
            
            results = self.execute_query(query, (computer_name, days))
            
            if results:
                latest = results[0]
                
                return {
                    'success': True,
                    'computer_name': computer_name,
                    'last_user': latest.get('UserName'),
                    'last_logon_time': latest.get('EventDateTime'),
                    'logon_type': latest.get('LogonType'),
                    'search_method': 'sql_server_events',
                    'connection_method': 'sql_query',
                    'computer_found': True,
                    'recent_logons': [
                        {
                            'user': r.get('UserName'),
                            'time': r.get('EventDateTime'),
                            'logon_type': r.get('LogonType'),
                            'source_ip': r.get('SourceIP'),
                            'logon_process': r.get('LogonProcess')
                        } for r in results
                    ],
                    'total_time': 0.5  # Estimado para SQL query
                }
            else:
                return {
                    'success': False,
                    'computer_name': computer_name,
                    'error': 'Nenhum evento de logon encontrado nos últimos dias',
                    'search_method': 'sql_server_events'
                }
                
        except Exception as e:
            logger.error(f"❌ Erro ao buscar eventos de logon para {computer_name}: {e}")
            return {
                'success': False,
                'computer_name': computer_name,
                'error': str(e),
                'search_method': 'sql_server_events'
            }


# Instância global
_sql_server_manager = None

def get_sql_server_manager() -> SQLServerManager:
    """Retorna instância singleton do SQLServerManager"""
    global _sql_server_manager
    if _sql_server_manager is None:
        _sql_server_manager = SQLServerManager()
    return _sql_server_manager

# Dependency para FastAPI
def get_sql_server() -> SQLServerManager:
    """Dependency para injeção do SQLServerManager no FastAPI"""
    return get_sql_server_manager()