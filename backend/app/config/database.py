import sqlite3
import logging
from contextlib import contextmanager
from typing import Optional, Dict, Any, List
import pyodbc
from datetime import datetime
from app.config.settings import get_settings
logger = logging.getLogger(__name__)

# SQL Server helper usando pyodbc (substitui uso prévio de SQLAlchemy)
def build_pyodbc_conn_str() -> Optional[str]:
    """Constroi uma connection string compatível com pyodbc a partir das settings.

    Retorna None se não houver configurações suficientes.
    """
    # Carrega as settings apenas quando necessário (evita validação em import-time)
    settings = get_settings()

    if not all([settings.SQL_SERVER_HOST, settings.SQL_SERVER_DATABASE,
                settings.SQL_SERVER_USERNAME, settings.SQL_SERVER_PASSWORD]):
        return None

    driver = settings.SQL_SERVER_DRIVER or "ODBC Driver 17 for SQL Server"
    # Monta a string DSNless que pyodbc entende (sem prefixo 'mssql+')
    conn_parts = [
        f"DRIVER={{{driver}}}",
        f"SERVER={settings.SQL_SERVER_HOST}",
        f"DATABASE={settings.SQL_SERVER_DATABASE}",
        f"UID={settings.SQL_SERVER_USERNAME}",
        f"PWD={settings.SQL_SERVER_PASSWORD}",
        "TrustServerCertificate=yes"
    ]

    return ";".join(conn_parts)


class SQLServerManager:
    """Gerenciador simples para conexões com SQL Server via pyodbc."""

    def __init__(self, conn_str: Optional[str] = None):
        self.conn_str = conn_str or build_pyodbc_conn_str()

    @contextmanager
    def get_connection(self):
        """Context manager que abre e fecha uma conexão pyodbc."""
        if not self.conn_str:
            raise RuntimeError("SQL Server connection string not configured")

        conn = pyodbc.connect(self.conn_str)
        try:
            yield conn
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Executa uma query SELECT no SQL Server e retorna uma lista de dicionários."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            columns = [col[0] for col in cursor.description] if cursor.description else []
            rows = cursor.fetchall()
            result = [dict(zip(columns, row)) for row in rows]
            return result

    def execute_write(self, query: str, params: tuple = None) -> int:
        """Executa INSERT/UPDATE/DELETE no SQL Server e retorna número de linhas afetadas."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return cursor.rowcount


# Instância singleton para SQL Server
_sql_server_manager: Optional[SQLServerManager] = None

def get_sql_server_manager() -> Optional[SQLServerManager]:
    global _sql_server_manager
    if _sql_server_manager is None:
        _sql_server_manager = SQLServerManager()
    return _sql_server_manager


class DatabaseManager:
    """Gerenciador de banco de dados SQLite"""
    
    def __init__(self, db_path: str = "warranties.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Inicializa o banco de dados com as tabelas necessárias"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Tabela principal de equipamentos
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS equipamentos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name VARCHAR(255) UNIQUE NOT NULL,
                        service_tag VARCHAR(50),
                        service_tag_limpo VARCHAR(50),
                        os TEXT,
                        os_version TEXT,
                        modelo TEXT,
                        data_expiracao DATE,
                        warranty_status VARCHAR(50),
                        warranty_end_date DATE,
                        ship_date DATE,
                        order_number VARCHAR(100),
                        description TEXT,
                        dns_hostname VARCHAR(255),
                        distinguished_name TEXT,
                        last_logon TIMESTAMP,
                        created_date TIMESTAMP,
                        disabled BOOLEAN DEFAULT 0,
                        user_account_control INTEGER,
                        primary_group_id INTEGER,
                        data_source VARCHAR(50),
                        ultima_consulta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        synced_from_ad BOOLEAN DEFAULT 0
                    )
                """)
                
                # Tabela de entitlements (garantias específicas)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS entitlements (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        equipamento_id INTEGER,
                        service_level_description TEXT,
                        service_level_code VARCHAR(50),
                        start_date DATE,
                        end_date DATE,
                        entitlement_type VARCHAR(100),
                        item_number VARCHAR(100),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (equipamento_id) REFERENCES equipamentos (id) ON DELETE CASCADE
                    )
                """)
                
                # Tabela de logs de consulta
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS warranty_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        service_tag VARCHAR(50),
                        computer_name VARCHAR(255),
                        status VARCHAR(20),
                        error_code VARCHAR(50),
                        error_message TEXT,
                        response_time_ms INTEGER,
                        consulta_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        api_endpoint VARCHAR(255),
                        user_agent TEXT
                    )
                """)
                
                # Tabela de estatísticas do dashboard (cache)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS dashboard_stats (
                        id INTEGER PRIMARY KEY,
                        total_computers INTEGER,
                        recent_logins INTEGER,
                        inactive_computers INTEGER,
                        os_distribution TEXT,  -- JSON string
                        warranty_summary TEXT, -- JSON string
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Tabela de cache de consultas DHCP
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS dhcp_cache (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        computer_name VARCHAR(255),
                        service_tag VARCHAR(50),
                        ship_name VARCHAR(50),
                        dhcp_server VARCHAR(50),
                        found BOOLEAN,
                        search_results TEXT, -- JSON string
                        filters_summary TEXT, -- JSON string
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP
                    )
                """)
                
                # Índices para performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_equipamentos_name ON equipamentos(name)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_equipamentos_service_tag ON equipamentos(service_tag)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_equipamentos_last_logon ON equipamentos(last_logon)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_equipamentos_warranty_status ON equipamentos(warranty_status)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_warranty_logs_timestamp ON warranty_logs(consulta_timestamp)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_dhcp_cache_computer ON dhcp_cache(computer_name)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_dhcp_cache_expires ON dhcp_cache(expires_at)")
                
                conn.commit()
                logger.info("✅ Banco de dados inicializado com sucesso!")
                
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar banco de dados: {e}")
            raise

    @contextmanager
    def get_connection(self):
        """Context manager para conexões de banco"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Permite acesso por nome de coluna
        try:
            yield conn
        finally:
            conn.close()

    def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Executa uma query SELECT e retorna os resultados"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                columns = [description[0] for description in cursor.description]
                rows = cursor.fetchall()
                
                return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.error(f"❌ Erro ao executar query: {e}")
            raise

    def execute_write(self, query: str, params: tuple = None) -> int:
        """Executa uma query INSERT/UPDATE/DELETE e retorna o número de linhas afetadas"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            logger.error(f"❌ Erro ao executar query de escrita: {e}")
            raise

    def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """Executa múltiplas queries com diferentes parâmetros"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.executemany(query, params_list)
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            logger.error(f"❌ Erro ao executar queries múltiplas: {e}")
            raise

    # =============================================================================
    # OPERAÇÕES ESPECÍFICAS DE COMPUTADORES
    # =============================================================================

    def get_computer_by_name(self, computer_name: str) -> Optional[Dict[str, Any]]:
        """Busca um computador por nome"""
        query = """
            SELECT * FROM equipamentos 
            WHERE UPPER(name) = UPPER(?) 
            LIMIT 1
        """
        results = self.execute_query(query, (computer_name,))
        return results[0] if results else None

    def get_computer_by_service_tag(self, service_tag: str) -> Optional[Dict[str, Any]]:
        """Busca um computador por service tag"""
        query = """
            SELECT * FROM equipamentos 
            WHERE UPPER(service_tag) = UPPER(?) OR UPPER(service_tag_limpo) = UPPER(?)
            LIMIT 1
        """
        results = self.execute_query(query, (service_tag, service_tag))
        return results[0] if results else None

    def get_all_computers(self, limit: int = None, offset: int = 0, 
                         filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Busca todos os computadores com filtros opcionais"""
        query_parts = ["SELECT * FROM equipamentos WHERE name IS NOT NULL AND name != ''"]
        params = []

        # Aplicar filtros
        if filters:
            if filters.get('status') == 'enabled':
                query_parts.append("AND disabled = 0")
            elif filters.get('status') == 'disabled':
                query_parts.append("AND disabled = 1")

            if filters.get('os') and filters['os'] != 'all':
                query_parts.append("AND UPPER(os) LIKE UPPER(?)")
                params.append(f"%{filters['os']}%")

            if filters.get('ou') and filters['ou'] != 'all':
                query_parts.append("AND UPPER(name) LIKE ?")
                params.append(f"{filters['ou']}%")

        # Ordenação
        query_parts.append("ORDER BY name ASC")

        # Paginação
        if limit:
            query_parts.append(f"LIMIT {limit}")
        if offset > 0:
            query_parts.append(f"OFFSET {offset}")

        query = " ".join(query_parts)
        return self.execute_query(query, tuple(params))

    def save_computer(self, computer_data: Dict[str, Any]) -> int:
        """Salva ou atualiza dados de um computador"""
        try:
            # Verificar se já existe
            existing = self.get_computer_by_name(computer_data['name'])
            
            if existing:
                # Atualizar
                query = """
                    UPDATE equipamentos SET
                        service_tag = ?, service_tag_limpo = ?, os = ?, os_version = ?,
                        modelo = ?, data_expiracao = ?, warranty_status = ?, warranty_end_date = ?,
                        ship_date = ?, order_number = ?, description = ?, dns_hostname = ?,
                        distinguished_name = ?, last_logon = ?, created_date = ?, disabled = ?,
                        user_account_control = ?, primary_group_id = ?, data_source = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """
                params = (
                    computer_data.get('service_tag'),
                    computer_data.get('service_tag_limpo'),
                    computer_data.get('os'),
                    computer_data.get('os_version'),
                    computer_data.get('modelo'),
                    computer_data.get('data_expiracao'),
                    computer_data.get('warranty_status'),
                    computer_data.get('warranty_end_date'),
                    computer_data.get('ship_date'),
                    computer_data.get('order_number'),
                    computer_data.get('description'),
                    computer_data.get('dns_hostname'),
                    computer_data.get('distinguished_name'),
                    computer_data.get('last_logon'),
                    computer_data.get('created_date'),
                    computer_data.get('disabled', False),
                    computer_data.get('user_account_control'),
                    computer_data.get('primary_group_id'),
                    computer_data.get('data_source'),
                    existing['id']
                )
                
                self.execute_write(query, params)
                return existing['id']
            else:
                # Inserir novo
                query = """
                    INSERT INTO equipamentos 
                    (name, service_tag, service_tag_limpo, os, os_version, modelo, 
                     data_expiracao, warranty_status, warranty_end_date, ship_date, 
                     order_number, description, dns_hostname, distinguished_name,
                     last_logon, created_date, disabled, user_account_control,
                     primary_group_id, data_source, synced_from_ad)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                params = (
                    computer_data['name'],
                    computer_data.get('service_tag'),
                    computer_data.get('service_tag_limpo'),
                    computer_data.get('os'),
                    computer_data.get('os_version'),
                    computer_data.get('modelo'),
                    computer_data.get('data_expiracao'),
                    computer_data.get('warranty_status'),
                    computer_data.get('warranty_end_date'),
                    computer_data.get('ship_date'),
                    computer_data.get('order_number'),
                    computer_data.get('description'),
                    computer_data.get('dns_hostname'),
                    computer_data.get('distinguished_name'),
                    computer_data.get('last_logon'),
                    computer_data.get('created_date'),
                    computer_data.get('disabled', False),
                    computer_data.get('user_account_control'),
                    computer_data.get('primary_group_id'),
                    computer_data.get('data_source'),
                    computer_data.get('synced_from_ad', False)
                )
                
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(query, params)
                    conn.commit()
                    return cursor.lastrowid

        except Exception as e:
            logger.error(f"❌ Erro ao salvar computador {computer_data.get('name', 'N/A')}: {e}")
            raise

    def bulk_insert_computers(self, computers_data: List[Dict[str, Any]]) -> int:
        """Insere múltiplos computadores de uma vez (mais eficiente)"""
        if not computers_data:
            return 0

        query = """
            INSERT OR REPLACE INTO equipamentos 
            (name, service_tag, service_tag_limpo, os, os_version, modelo, 
             description, dns_hostname, distinguished_name, last_logon, 
             created_date, disabled, user_account_control, primary_group_id, 
             data_source, synced_from_ad, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """

        params_list = []
        for computer in computers_data:
            params_list.append((
                computer['name'],
                computer.get('service_tag'),
                computer.get('service_tag_limpo'),
                computer.get('os'),
                computer.get('os_version'),
                computer.get('modelo'),
                computer.get('description'),
                computer.get('dns_hostname'),
                computer.get('distinguished_name'),
                computer.get('last_logon'),
                computer.get('created_date'),
                computer.get('disabled', False),
                computer.get('user_account_control'),
                computer.get('primary_group_id'),
                computer.get('data_source', 'ad'),
                computer.get('synced_from_ad', True)
            ))

        return self.execute_many(query, params_list)

    def delete_non_synced_computers(self) -> int:
        """Remove computadores que não foram sincronizados na última operação"""
        query = "DELETE FROM equipamentos WHERE synced_from_ad = 0"
        return self.execute_write(query)

    def mark_all_computers_as_not_synced(self) -> int:
        """Marca todos os computadores como não sincronizados"""
        query = "UPDATE equipamentos SET synced_from_ad = 0"
        return self.execute_write(query)

    # =============================================================================
    # OPERAÇÕES ESPECÍFICAS DE GARANTIAS
    # =============================================================================

    def save_warranty_info(self, warranty_data: Dict[str, Any], computer_id: int) -> bool:
        """Salva informações de garantia para um computador"""
        try:
            # Atualizar dados de garantia no equipamento
            query = """
                UPDATE equipamentos SET
                    service_tag = COALESCE(?, service_tag),
                    service_tag_limpo = ?, 
                    modelo = COALESCE(?, modelo),
                    warranty_status = ?,
                    warranty_end_date = ?,
                    data_expiracao = ?,
                    ship_date = ?,
                    order_number = ?,
                    data_source = ?,
                    ultima_consulta = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """
            
            params = (
                warranty_data.get('serviceTag'),
                warranty_data.get('serviceTagLimpo'),
                warranty_data.get('modelo'),
                warranty_data.get('status'),
                warranty_data.get('warrantyEndDate'),
                warranty_data.get('dataExpiracao'),
                warranty_data.get('shipDate'),
                warranty_data.get('orderNumber'),
                warranty_data.get('dataSource', 'dell_api'),
                computer_id
            )
            
            self.execute_write(query, params)

            # Limpar entitlements antigos
            self.execute_write("DELETE FROM entitlements WHERE equipamento_id = ?", (computer_id,))

            # Inserir novos entitlements
            if warranty_data.get('entitlements'):
                entitlements_query = """
                    INSERT INTO entitlements 
                    (equipamento_id, service_level_description, service_level_code,
                     start_date, end_date, entitlement_type, item_number)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """
                
                entitlements_params = []
                for ent in warranty_data['entitlements']:
                    entitlements_params.append((
                        computer_id,
                        ent.get('serviceLevelDescription'),
                        ent.get('serviceLevelCode'),
                        ent.get('startDate'),
                        ent.get('endDate'),
                        ent.get('entitlementType'),
                        ent.get('itemNumber')
                    ))
                
                self.execute_many(entitlements_query, entitlements_params)

            return True

        except Exception as e:
            logger.error(f"❌ Erro ao salvar garantia para computador {computer_id}: {e}")
            return False

    def get_warranty_summary(self) -> List[Dict[str, Any]]:
        """Retorna resumo de todas as garantias"""
        query = """
            SELECT 
                e.id as computer_id,
                e.name as computer_name,
                e.service_tag,
                e.warranty_status,
                e.warranty_end_date,
                e.modelo as model,
                e.ultima_consulta as last_checked
            FROM equipamentos e
            WHERE e.name IS NOT NULL AND e.name != ''
            ORDER BY e.warranty_end_date ASC NULLS LAST, e.name ASC
        """
        return self.execute_query(query)

    def get_expiring_warranties(self, days: int = 30) -> List[Dict[str, Any]]:
        """Retorna garantias expirando em X dias"""
        query = """
            SELECT 
                name as computer_name,
                service_tag,
                modelo as model,
                warranty_end_date,
                warranty_status,
                (julianday(warranty_end_date) - julianday('now')) as days_remaining
            FROM equipamentos 
            WHERE warranty_end_date BETWEEN DATE('now') AND DATE('now', '+' || ? || ' days')
            AND warranty_status = 'Em garantia'
            ORDER BY warranty_end_date ASC
        """
        return self.execute_query(query, (days,))

    # =============================================================================
    # OPERAÇÕES DE LOGS
    # =============================================================================

    def log_warranty_query(self, service_tag: str, computer_name: str = None, 
                          status: str = "SUCCESS", error_code: str = None, 
                          error_message: str = None, response_time_ms: int = 0,
                          api_endpoint: str = None, user_agent: str = None) -> int:
        """Registra log de consulta de garantia"""
        query = """
            INSERT INTO warranty_logs 
            (service_tag, computer_name, status, error_code, error_message, 
             response_time_ms, api_endpoint, user_agent)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            service_tag, computer_name, status, error_code, 
            error_message, response_time_ms, api_endpoint, user_agent
        )
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid

    def get_warranty_logs(self, limit: int = 100, service_tag: str = None) -> List[Dict[str, Any]]:
        """Retorna logs das consultas de garantia"""
        query = """
            SELECT service_tag, computer_name, status, error_code, error_message, 
                   response_time_ms, api_endpoint, consulta_timestamp
            FROM warranty_logs
        """
        params = []

        if service_tag:
            query += " WHERE UPPER(service_tag) = UPPER(?)"
            params.append(service_tag)

        query += " ORDER BY consulta_timestamp DESC LIMIT ?"
        params.append(limit)

        return self.execute_query(query, tuple(params))

    def cleanup_old_logs(self, days_to_keep: int = 90) -> int:
        """Remove logs antigos para manter o banco limpo"""
        query = """
            DELETE FROM warranty_logs 
            WHERE consulta_timestamp < DATE('now', '-' || ? || ' days')
        """
        return self.execute_write(query, (days_to_keep,))

    # =============================================================================
    # OPERAÇÕES DE CACHE DHCP
    # =============================================================================

    def save_dhcp_cache(self, computer_name: str, service_tag: str, 
                       dhcp_info: Dict[str, Any], expires_minutes: int = 60) -> int:
        """Salva informações DHCP no cache"""
        try:
            import json
            from datetime import datetime, timedelta

            expires_at = datetime.now() + timedelta(minutes=expires_minutes)
            
            query = """
                INSERT OR REPLACE INTO dhcp_cache
                (computer_name, service_tag, ship_name, dhcp_server, found,
                 search_results, filters_summary, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                computer_name,
                service_tag,
                dhcp_info.get('ship_name'),
                dhcp_info.get('dhcp_server'),
                dhcp_info.get('service_tag_found', False),
                json.dumps(dhcp_info.get('search_results', [])),
                json.dumps(dhcp_info.get('filters', {})),
                expires_at.isoformat()
            )
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                return cursor.lastrowid

        except Exception as e:
            logger.warning(f"⚠️ Erro ao salvar cache DHCP: {e}")
            return 0

    def get_dhcp_cache(self, computer_name: str) -> Optional[Dict[str, Any]]:
        """Busca informações DHCP do cache se ainda válidas"""
        try:
            import json
            
            query = """
                SELECT * FROM dhcp_cache 
                WHERE UPPER(computer_name) = UPPER(?) 
                AND expires_at > DATETIME('now')
                ORDER BY last_updated DESC
                LIMIT 1
            """
            
            results = self.execute_query(query, (computer_name,))
            
            if results:
                result = results[0]
                
                # Parse JSON fields
                search_results = json.loads(result['search_results']) if result['search_results'] else []
                filters_summary = json.loads(result['filters_summary']) if result['filters_summary'] else {}
                
                return {
                    'ship_name': result['ship_name'],
                    'dhcp_server': result['dhcp_server'],
                    'service_tag_found': bool(result['found']),
                    'search_results': search_results,
                    'filters': filters_summary,
                    'timestamp': result['last_updated'],
                    'source': 'cache'
                }

        except Exception as e:
            logger.warning(f"⚠️ Erro ao buscar cache DHCP: {e}")
            
        return None

    def cleanup_expired_dhcp_cache(self) -> int:
        """Remove entradas expiradas do cache DHCP"""
        query = "DELETE FROM dhcp_cache WHERE expires_at <= DATETIME('now')"
        return self.execute_write(query)

    # =============================================================================
    # OPERAÇÕES DE ESTATÍSTICAS
    # =============================================================================

    def get_computers_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas gerais dos computadores"""
        query = """
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN disabled = 0 THEN 1 END) as enabled,
                COUNT(CASE WHEN disabled = 1 THEN 1 END) as disabled,
                COUNT(CASE WHEN last_logon > datetime('now', '-7 days') THEN 1 END) as recent_logins,
                COUNT(CASE WHEN last_logon <= datetime('now', '-30 days') OR last_logon IS NULL THEN 1 END) as inactive,
                COUNT(CASE WHEN last_logon IS NULL THEN 1 END) as never_logged,
                COUNT(CASE WHEN warranty_status = 'Em garantia' OR warranty_status = 'Active' THEN 1 END) as warranty_active,
                COUNT(CASE WHEN warranty_status = 'Expirado' OR warranty_status = 'Expired' THEN 1 END) as warranty_expired
            FROM equipamentos
            WHERE name IS NOT NULL AND name != ''
        """
        
        results = self.execute_query(query)
        return results[0] if results else {}

    def get_os_distribution(self) -> List[Dict[str, Any]]:
        """Retorna distribuição por sistema operacional"""
        query = """
            SELECT os as name, COUNT(*) as value
            FROM equipamentos 
            WHERE os IS NOT NULL AND os != '' AND os != 'N/A'
            GROUP BY os
            ORDER BY value DESC
            LIMIT 15
        """
        return self.execute_query(query)

    # =============================================================================
    # UTILITIES E MANUTENÇÃO
    # =============================================================================

    def vacuum_database(self):
        """Otimiza o banco de dados SQLite"""
        try:
            with self.get_connection() as conn:
                conn.execute("VACUUM")
                logger.info("🧹 Banco de dados otimizado (VACUUM)")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao otimizar banco: {e}")

    def get_database_size(self) -> Dict[str, Any]:
        """Retorna informações sobre o tamanho do banco"""
        try:
            import os
            
            if os.path.exists(self.db_path):
                size_bytes = os.path.getsize(self.db_path)
                size_mb = size_bytes / (1024 * 1024)
                
                # Contar registros por tabela
                tables_info = {}
                tables = ['equipamentos', 'entitlements', 'warranty_logs', 'dhcp_cache', 'dashboard_stats']
                
                for table in tables:
                    try:
                        result = self.execute_query(f"SELECT COUNT(*) as count FROM {table}")
                        tables_info[table] = result[0]['count'] if result else 0
                    except:
                        tables_info[table] = 0
                
                return {
                    'file_size_bytes': size_bytes,
                    'file_size_mb': round(size_mb, 2),
                    'tables': tables_info
                }
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter tamanho do banco: {e}")
            
        return {'error': 'Não foi possível obter informações do banco'}

    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do banco de dados"""
        try:
            # Teste de conexão
            test_query = "SELECT 1 as test"
            result = self.execute_query(test_query)
            
            if result and result[0]['test'] == 1:
                stats = self.get_computers_stats()
                db_size = self.get_database_size()
                
                return {
                    'status': 'healthy',
                    'connection': 'ok',
                    'total_computers': stats.get('total', 0),
                    'database_size_mb': db_size.get('file_size_mb', 0),
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {'status': 'unhealthy', 'error': 'Teste de conexão falhou'}
                
        except Exception as e:
            logger.error(f"❌ Erro no health check do banco: {e}")
            return {'status': 'unhealthy', 'error': str(e)}


# Instância global (singleton pattern)
_db_manager = None

def get_database_manager() -> DatabaseManager:
    """Retorna instância singleton do DatabaseManager"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


# Dependency para FastAPI
def get_db() -> DatabaseManager:
    """Dependency para injeção do DatabaseManager no FastAPI"""
    return get_database_manager()