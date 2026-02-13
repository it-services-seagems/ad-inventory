import pyodbc
import logging
from datetime import datetime, timedelta
from ..config import SQL_SERVER, SQL_DATABASE, SQL_USERNAME, SQL_PASSWORD, USE_WINDOWS_AUTH
import os

logger = logging.getLogger(__name__)


class SQLManager:
    def __init__(self):
        self.connection_string = self._build_connection_string()
        try:
            self._test_connection()
        except Exception:
            logger.exception('SQL test connection failed on init')

    def _build_connection_string(self):
        """Build a connection string.

        Behavior:
        - If env var SQL_ODBC_DRIVER is set, use it.
        - Otherwise autodetect available ODBC drivers and prefer:
          ODBC Driver 18 for SQL Server -> ODBC Driver 17 for SQL Server -> SQL Server Native Client 11.0
        - If Driver 18 is selected, include sensible Encrypt/TrustServerCertificate defaults which can be overridden
          via SQL_ODBC_ENCRYPT env var ('yes'/'no').
        """
        # Allow manual override
        env_driver = os.getenv('SQL_ODBC_DRIVER')
        driver = None
        if env_driver:
            driver = env_driver
        else:
            try:
                available = list(pyodbc.drivers())
            except Exception:
                available = []

            # preference order
            for candidate in ('ODBC Driver 18 for SQL Server', 'ODBC Driver 17 for SQL Server', 'SQL Server Native Client 11.0'):
                if candidate in available:
                    driver = candidate
                    break

            # fallback: pick first driver that mentions SQL Server
            if not driver:
                for d in available:
                    if 'SQL Server' in d:
                        driver = d
                        break

            # final fallback: use a common name (this may still fail if driver absent)
            if not driver:
                driver = 'ODBC Driver 17 for SQL Server'

        # Driver-specific options (Driver 18 may require TLS settings)
        encrypt_env = os.getenv('SQL_ODBC_ENCRYPT')
        encrypt_part = ''
        if driver and driver.startswith('ODBC Driver 18'):
            # default to no encryption but trust server certificate to avoid handshake problems on internal networks
            if encrypt_env is None:
                encrypt_part = 'Encrypt=no;TrustServerCertificate=yes;'
            else:
                if encrypt_env.lower() in ('1', 'true', 'yes'):
                    encrypt_part = 'Encrypt=yes;TrustServerCertificate=yes;'
                else:
                    encrypt_part = 'Encrypt=no;TrustServerCertificate=yes;'

        if USE_WINDOWS_AUTH:
            return f"DRIVER={{{driver}}};SERVER={SQL_SERVER};DATABASE={SQL_DATABASE};{encrypt_part}Trusted_Connection=yes;"
        else:
            return f"DRIVER={{{driver}}};SERVER={SQL_SERVER};DATABASE={SQL_DATABASE};UID={SQL_USERNAME};PWD={SQL_PASSWORD};{encrypt_part}"

    def _test_connection(self):
        with pyodbc.connect(self.connection_string) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1')
            logger.info(f"✅ Conexão SQL Server estabelecida: {SQL_SERVER}/{SQL_DATABASE}")

    def get_connection(self):
        return pyodbc.connect(self.connection_string)

    def execute_query(self, query, params=None, fetch=True):
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
        except Exception:
            logger.exception('SQL execute_query failed')
            raise

    # Minimal compatibility methods used by routers
    def get_computers_from_sql(self, inventory_filter=None):
        # Build a resilient select that only references columns that exist in the computers table
        try:
            # helper to format datetime-like values safely
            def _format_dt(v):
                if v is None:
                    return None
                # already a datetime
                if isinstance(v, datetime):
                    return v.isoformat()
                # strings: try parsing common SQL datetime formats to isoformat, otherwise return as-is
                if isinstance(v, str):
                    try:
                        # try ISO-like strings first (replace space with T)
                        return datetime.fromisoformat(v.replace(' ', 'T')).isoformat()
                    except Exception:
                        try:
                            return datetime.strptime(v, '%Y-%m-%d %H:%M:%S.%f').isoformat()
                        except Exception:
                            try:
                                return datetime.strptime(v, '%Y-%m-%d %H:%M:%S').isoformat()
                            except Exception:
                                # leave the original string if we can't parse it
                                return v
                # numeric timestamps
                if isinstance(v, (int, float)):
                    try:
                        return datetime.fromtimestamp(v).isoformat()
                    except Exception:
                        return str(v)
                # fallback to string representation
                try:
                    return str(v)
                except Exception:
                    return None
            # Inspect available columns from computers table
            try:
                cols_info = self.execute_query("SELECT TOP 0 * FROM computers")
                # execute_query returns [] for top 0 rows, but cursor.description was used earlier to build columns
                # Fallback to using a direct connection when needed
                with self.get_connection() as conn:
                    cur = conn.cursor()
                    cur.execute("SELECT TOP 0 * FROM computers")
                    columns = [c[0].lower() for c in cur.description] if cur.description else []
            except Exception:
                logger.exception('Failed to inspect computers columns; falling back to minimal query')
                columns = []

            has = lambda name: name.lower() in columns

            select_cols = [
                'c.id', 'c.name', 'c.dns_hostname', 'c.distinguished_name as dn',
                'c.is_enabled', 'c.is_domain_controller', 'c.description',
                'c.last_logon_timestamp as lastLogon', 'c.created_date as created',
                'c.user_account_control', 'c.primary_group_id', 'c.last_sync_ad'
            ]

            if has('ip_address'):
                select_cols.append('c.ip_address')
            if has('mac_address'):
                select_cols.append('c.mac_address')
            if has('usuario_atual'):
                select_cols.append('c.usuario_atual')
            if has('usuario_anterior'):
                select_cols.append('c.usuario_anterior')
            if has('status'):
                select_cols.append('c.status')
            if has('location'):
                select_cols.append('c.location')

            # OS and organization joins are optional but safe to include; OS fields come from separate table
            select_cols.append('os.name as os')
            select_cols.append('os.version as osVersion')
            select_clause = ',\n            '.join(select_cols)

            base_query = f"""
            SELECT TOP 1000
            {select_clause}
            FROM computers c
            LEFT JOIN organizations o ON c.organization_id = o.id
            LEFT JOIN operating_systems os ON c.operating_system_id = os.id
            WHERE c.is_domain_controller = 0
            """

            if inventory_filter == 'spare':
                query = base_query + " AND c.status = 'Spare' ORDER BY c.name"
            else:
                query = base_query + " ORDER BY c.name"

            rows = self.execute_query(query)
            computers = []
            for r in rows:
                try:
                    computers.append({
                        'id': r.get('id'),
                        'name': r.get('name'),
                        'dn': r.get('dn'),
                        'lastLogon': _format_dt(r.get('lastLogon')),
                        'os': r.get('os') or 'N/A',
                        'osVersion': r.get('osVersion') or 'N/A',
                        'created': _format_dt(r.get('created')),
                        'description': r.get('description') or '',
                        'disabled': not bool(r.get('is_enabled')),
                        'userAccountControl': r.get('user_account_control') or 0,
                        'primaryGroupID': r.get('primary_group_id') or 515,
                        'dnsHostName': r.get('dns_hostname') or '',
                        'ipAddress': r.get('ip_address') if has('ip_address') else '',
                        'macAddress': r.get('mac_address') if has('mac_address') else '',
                        'usuarioAtual': r.get('usuario_atual') if has('usuario_atual') else '',
                        'usuarioAnterior': r.get('usuario_anterior') if has('usuario_anterior') else '',
                        'inventoryStatus': r.get('status') if has('status') else '',
                        'location': r.get('location') if has('location') else '',
                        'organizationName': r.get('organization_name') or '',
                        'organizationCode': r.get('organization_code') or ''
                    })
                except Exception:
                    logger.exception('Error processing computer row')
                    continue
            return computers
        except Exception:
            logger.exception('get_computers_from_sql failed')
            return []

    def sync_computer_to_sql(self, computer_data):
        """Sincroniza um computador do AD para o SQL Server"""
        try:
            if not computer_data:
                return None

            name = computer_data.get('name')
            if not name:
                return None

            # Verificar se o computador já existe
            check_query = "SELECT id FROM computers WHERE name = ?"
            existing = self.execute_query(check_query, [name])
            
            # Preparar dados básicos para inserção/atualização
            dns_hostname = computer_data.get('dNSHostName', '')
            distinguished_name = computer_data.get('distinguishedName', '')
            description = computer_data.get('description', '')
            is_enabled = bool(computer_data.get('userAccountControl', 0) & 0x0002 == 0)  # ACCOUNTDISABLE flag
            user_account_control = computer_data.get('userAccountControl', 0)
            primary_group_id = computer_data.get('primaryGroupID', 515)
            sam_account_name = computer_data.get('sAMAccountName', name)
            
            # Processar timestamps
            last_logon = computer_data.get('lastLogonTimestamp')
            created_date = computer_data.get('whenCreated')
            
            if existing:
                # Atualizar computador existente - PRESERVAR dados de usuário
                update_query = """
                UPDATE computers 
                SET dns_hostname = ?,
                    distinguished_name = ?,
                    description = ?,
                    is_enabled = ?,
                    user_account_control = ?,
                    primary_group_id = ?,
                    sam_account_name = ?,
                    last_logon_timestamp = ?,
                    last_sync_ad = GETDATE(),
                    updated_at = GETDATE()
                WHERE name = ?
                """
                params = [
                    dns_hostname,
                    distinguished_name, 
                    description,
                    is_enabled,
                    user_account_control,
                    primary_group_id,
                    sam_account_name,
                    last_logon,
                    name
                ]
                
                self.execute_query(update_query, params, fetch=False)
                return existing[0]['id']  # Retorna ID existente (atualização)
                
            else:
                # Inserir novo computador
                insert_query = """
                INSERT INTO computers (
                    name, dns_hostname, distinguished_name, description,
                    is_enabled, is_domain_controller, user_account_control,
                    primary_group_id, sam_account_name, last_logon_timestamp, 
                    created_date, last_sync_ad, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE(), GETDATE())
                """
                params = [
                    name,
                    dns_hostname,
                    distinguished_name,
                    description,
                    is_enabled,
                    False,  # is_domain_controller
                    user_account_control,
                    primary_group_id,
                    sam_account_name,
                    last_logon,
                    created_date
                ]
                
                self.execute_query(insert_query, params, fetch=False)
                
                # Buscar o ID do registro inserido
                new_record = self.execute_query("SELECT id FROM computers WHERE name = ?", [name])
                return new_record[0]['id'] if new_record else None  # Retorna None (nova inserção)
                
        except Exception as e:
            logger.exception(f'Erro ao sincronizar computador {computer_data.get("name", "unknown")}: {e}')
            return None

    def update_computer_status_in_sql(self, computer_name, is_enabled, user_account_control=None):
        try:
            query = "UPDATE computers SET is_enabled = ?, user_account_control = COALESCE(?, user_account_control), last_modified = GETDATE() WHERE name = ?"
            params = (1 if is_enabled else 0, user_account_control, computer_name)
            rows = self.execute_query(query, params, fetch=False)
            return rows > 0
        except Exception:
            logger.exception('update_computer_status_in_sql failed')
            return False

    def extract_service_tag_from_computer_name(self, computer_name):
        """Extrai service tag do nome da máquina (baseado no debug_c1wsb92.py)"""
        if not computer_name:
            return None
            
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

    def get_all_computers(self):
        """Retorna todos os computadores da base de dados"""
        try:
            query = "SELECT * FROM dbo.computers ORDER BY name"
            return self.execute_query(query)
        except Exception as e:
            logger.exception(f'Erro ao buscar todos os computadores: {e}')
            return []

    def clear_computers_table(self):
        """Limpa completamente a tabela de computadores"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM dbo.computers")
            conn.commit()
            cursor.close()
            conn.close()
            logger.info('✅ Tabela de computadores limpa')
        except Exception as e:
            logger.exception(f'Erro ao limpar tabela de computadores: {e}')
            raise

    def log_sync_operation(self, sync_type, status, stats):
        """Registra operação de sincronização no log"""
        try:
            logger.info(f'📊 Sync {sync_type} {status}: {stats}')
            # Opcionalmente, você pode salvar essas informações em uma tabela de log se existir
            # Por enquanto, apenas registra no log
        except Exception as e:
            logger.exception(f'Erro ao registrar operação de sync: {e}')

    def get_current_user_by_service_tag(self, service_tag):
        """Busca o usuário atual usando o service tag da máquina"""
        if not service_tag:
            return None
            
        try:
            # Normalizar service tag
            service_tag = service_tag.upper().strip()
            
            # Query para buscar usuário pelo service tag
            # Primeiro tenta buscar diretamente pelo service tag na tabela computers
            query = """
            SELECT TOP 1 
                c.name,
                c.usuario_atual,
                c.usuario_anterior,
                c.description,
                c.last_logon_timestamp
            FROM computers c
            WHERE UPPER(c.name) LIKE ?
               OR UPPER(c.name) LIKE ?
               OR UPPER(c.name) LIKE ?
               OR UPPER(c.name) LIKE ?
               OR UPPER(c.name) LIKE ?
               OR UPPER(c.name) LIKE ?
               OR UPPER(c.name) LIKE ?
               OR UPPER(c.name) LIKE ?
               OR UPPER(c.name) = ?
            ORDER BY c.last_logon_timestamp DESC
            """
            
            # Gerar padrões de busca para os prefixos conhecidos + service tag
            prefixes = ['SHQ', 'ESM', 'DIA', 'TOP', 'RUB', 'JAD', 'ONI', 'CLO']
            params = []
            
            # Adicionar padrões com prefixos
            for prefix in prefixes:
                params.append(f"{prefix}{service_tag}")
            
            # Adicionar service tag sem prefixo
            params.append(service_tag)
            
            rows = self.execute_query(query, params=params)
            
            if rows:
                row = rows[0]
                return {
                    'computer_name': row.get('name'),
                    'usuario_atual': row.get('usuario_atual'),
                    'usuario_anterior': row.get('usuario_anterior'),
                    'description': row.get('description'),
                    'last_logon': row.get('last_logon_timestamp'),
                    'found': True
                }
            else:
                return {
                    'found': False,
                    'usuario_atual': None,
                    'message': f'Máquina com service tag {service_tag} não encontrada'
                }
                
        except Exception as e:
            logger.exception(f'Erro ao buscar usuário por service tag {service_tag}')
            return {
                'found': False,
                'usuario_atual': None,
                'error': str(e)
            }

    def get_computers_for_warranty_update(self):
        """Get computers that need warranty updates (baseado no debug_c1wsb92.py) - Optimized"""
        try:
            # Query otimizada que extrai service tags diretamente no SQL
            query = """
            SELECT 
                c.id,
                c.name,
                c.description,
                -- Extract service tag directly in SQL for better performance
                CASE 
                    WHEN c.name LIKE 'SHQ%' AND LEN(c.name) > 8 THEN SUBSTRING(c.name, 4, LEN(c.name))
                    WHEN c.name LIKE 'ESM%' AND LEN(c.name) > 8 THEN SUBSTRING(c.name, 4, LEN(c.name))
                    WHEN c.name LIKE 'DIA%' AND LEN(c.name) > 8 THEN SUBSTRING(c.name, 4, LEN(c.name))
                    WHEN c.name LIKE 'TOP%' AND LEN(c.name) > 8 THEN SUBSTRING(c.name, 4, LEN(c.name))
                    WHEN c.name LIKE 'RUB%' AND LEN(c.name) > 8 THEN SUBSTRING(c.name, 4, LEN(c.name))
                    WHEN c.name LIKE 'JAD%' AND LEN(c.name) > 8 THEN SUBSTRING(c.name, 4, LEN(c.name))
                    WHEN c.name LIKE 'ONI%' AND LEN(c.name) > 8 THEN SUBSTRING(c.name, 4, LEN(c.name))
                    WHEN c.name LIKE 'CLO%' AND LEN(c.name) > 8 THEN SUBSTRING(c.name, 4, LEN(c.name))
                    WHEN LEN(c.name) >= 5 THEN c.name
                    ELSE NULL
                END as extracted_service_tag,
                dw.id as warranty_id,
                dw.last_updated,
                dw.cache_expires_at,
                dw.warranty_status,
                dw.last_error,
                CASE 
                    WHEN dw.cache_expires_at IS NULL OR dw.cache_expires_at < GETDATE() OR dw.last_error IS NOT NULL 
                    THEN 1 ELSE 0 
                END as needs_update
            FROM computers c
            LEFT JOIN dell_warranty dw ON c.id = dw.computer_id
            WHERE c.is_domain_controller = 0
                AND c.name IS NOT NULL
                AND LEN(c.name) >= 5
            ORDER BY 
                CASE WHEN dw.cache_expires_at IS NULL OR dw.cache_expires_at < GETDATE() THEN 0 ELSE 1 END,
                c.name
            """
            
            rows = self.execute_query(query)
            logger.info(f"Found {len(rows)} computers in database")
            
            # Filter only computers with valid service tags
            computers = []
            for row in rows:
                service_tag = row.get('extracted_service_tag')
                if service_tag and len(service_tag) >= 5:
                    computers.append({
                        'id': row['id'],
                        'name': row['name'],
                        'service_tag': service_tag,
                        'warranty_id': row['warranty_id'],
                        'last_updated': row['last_updated'],
                        'cache_expires_at': row['cache_expires_at'],
                        'warranty_status': row['warranty_status'],
                        'last_error': row['last_error'],
                        'needs_update': bool(row['needs_update'])
                    })
            
            logger.info(f"Found {len(computers)} computers with valid service tags")
            needs_update_count = sum(1 for c in computers if c['needs_update'])
            logger.info(f"{needs_update_count} need warranty updates")
            
            return computers
            
        except Exception:
            logger.exception('get_computers_for_warranty_update failed')
            return []

    def save_warranty_to_database(self, computer_id, warranty_data):
        """Save warranty information to database (baseado no debug_c1wsb92.py)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # Discover which columns exist in the table to be resilient across schema versions
                try:
                    cursor.execute("SELECT TOP 0 * FROM dell_warranty")
                    existing_columns = [c[0].lower() for c in cursor.description] if cursor.description else []
                except Exception:
                    # If table doesn't exist or another error, log and re-raise to be visible
                    logger.exception('Failed to inspect dell_warranty columns')
                    raise

                cols_set = set(existing_columns)

                def _has(col):
                    return col.lower() in cols_set

                # Helper to check existence of a row by computer_id
                row_exists = False
                if _has('computer_id'):
                    try:
                        cursor.execute("SELECT id FROM dell_warranty WHERE computer_id = ?", (computer_id,))
                        row_exists = cursor.fetchone() is not None
                    except Exception:
                        # If this fails, keep going but mark as not existing
                        logger.exception('Failed to check existing dell_warranty row')
                        row_exists = False

                if warranty_data.get('success'):
                    # Build a map of candidate columns -> values
                    candidates = {
                        'service_tag': warranty_data.get('service_tag'),
                        'service_tag_clean': warranty_data.get('service_tag_clean'),
                        'warranty_start_date': warranty_data.get('warranty_start_date'),
                        'warranty_end_date': warranty_data.get('warranty_end_date'),
                        'warranty_status': warranty_data.get('warranty_status'),
                        'product_line_description': warranty_data.get('product_line_description'),
                        'system_description': warranty_data.get('system_description'),
                        'ship_date': warranty_data.get('ship_date'),
                        'order_number': warranty_data.get('order_number'),
                        'entitlements': warranty_data.get('entitlements'),
                        'cache_expires_at': warranty_data.get('cache_expires_at')
                    }

                    # Filter only columns that exist
                    to_set = {k: v for k, v in candidates.items() if _has(k)}

                    if row_exists:
                        # UPDATE: set available columns and update last_updated/last_error when possible
                        set_parts = []
                        params = []
                        for col, val in to_set.items():
                            set_parts.append(f"{col} = ?")
                            params.append(val)

                        if _has('last_updated'):
                            set_parts.append('last_updated = GETDATE()')
                        if _has('last_error'):
                            set_parts.append('last_error = NULL')

                        if not set_parts:
                            # Nothing to update, return True
                            logger.info('No matching columns to update in dell_warranty; skipping update')
                            return True

                        update_query = f"UPDATE dell_warranty SET {', '.join(set_parts)} WHERE computer_id = ?"
                        params.append(computer_id)
                        cursor.execute(update_query, tuple(params))
                    else:
                        # INSERT: build column list dynamically
                        insert_cols = ['computer_id'] if _has('computer_id') else []
                        insert_vals = [computer_id] if _has('computer_id') else []
                        for col, val in to_set.items():
                            insert_cols.append(col)
                            insert_vals.append(val)

                        if _has('last_updated'):
                            insert_cols.append('last_updated')
                            insert_vals.append(None)  # will use GETDATE() in SQL if possible
                        if _has('cache_expires_at') and 'cache_expires_at' not in to_set:
                            # ensure cache_expires_at present if available (could be None)
                            insert_cols.append('cache_expires_at')
                            insert_vals.append(warranty_data.get('cache_expires_at'))

                        if not insert_cols:
                            logger.info('No matching columns to insert into dell_warranty; skipping insert')
                            return True

                        # Build parameter placeholders
                        placeholders = ', '.join(['?'] * len(insert_cols))
                        cols_sql = ', '.join(insert_cols)

                        # If last_updated exists, try to set it to GETDATE() in SQL by building specialized query
                        if _has('last_updated'):
                            # replace the corresponding placeholder with GETDATE() in the VALUES clause
                            # simple approach: build VALUES with ? for all and then update last_updated with GETDATE() afterwards
                            insert_query = f"INSERT INTO dell_warranty ({cols_sql}) VALUES ({placeholders})"
                            cursor.execute(insert_query, tuple(insert_vals))
                            # If GETDATE() desired and supported in the schema, update the inserted row's last_updated
                            if _has('last_updated') and _has('computer_id'):
                                try:
                                    cursor.execute("UPDATE dell_warranty SET last_updated = GETDATE() WHERE computer_id = ?", (computer_id,))
                                except Exception:
                                    # ignore
                                    pass
                        else:
                            insert_query = f"INSERT INTO dell_warranty ({cols_sql}) VALUES ({placeholders})"
                            cursor.execute(insert_query, tuple(insert_vals))

                else:
                    # Error case: record the last_error and set a retry time
                    from datetime import timedelta
                    retry_time = datetime.now() + timedelta(hours=6)

                    if row_exists and _has('cache_expires_at') and _has('last_error'):
                        update_query = "UPDATE dell_warranty SET last_updated = GETDATE(), cache_expires_at = ?, last_error = ? WHERE computer_id = ?"
                        params = (retry_time, f"{warranty_data.get('code', 'ERROR')}: {warranty_data.get('error', 'Unknown error')}", computer_id)
                        cursor.execute(update_query, params)
                    elif not row_exists and _has('computer_id') and _has('last_error'):
                        insert_cols = ['computer_id', 'last_updated', 'cache_expires_at', 'last_error']
                        placeholders = ', '.join(['?'] * len(insert_cols))
                        insert_query = f"INSERT INTO dell_warranty ({', '.join(insert_cols)}) VALUES ({placeholders})"
                        params = (computer_id, datetime.now(), retry_time, f"{warranty_data.get('code', 'ERROR')}: {warranty_data.get('error', 'Unknown error')}")
                        cursor.execute(insert_query, params)
                    else:
                        # No useful columns to record error; log and skip
                        logger.warning('No matching columns to record warranty error for computer_id %s', computer_id)

                conn.commit()
                return True
                
        except Exception:
            logger.exception(f'save_warranty_to_database failed for computer_id {computer_id}')
            return False


# Singleton instance for use throughout FastAPI
sql_manager = SQLManager()
