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
                    # Auto-detect non-SELECT statements to avoid fetchall() on UPDATE/INSERT/DELETE
                    if cursor.description is None:
                        # No result set — this was a DML statement; commit and return rowcount
                        conn.commit()
                        return cursor.rowcount
                    columns = [column[0] for column in cursor.description]
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

            # Inspect dell_warranty table columns (optional)
            try:
                with self.get_connection() as conn:
                    cur = conn.cursor()
                    cur.execute("SELECT TOP 0 * FROM dell_warranty")
                    dell_columns = [c[0].lower() for c in cur.description] if cur.description else []
            except Exception:
                dell_columns = []

            has = lambda name: name.lower() in columns
            has_dw = lambda name: name.lower() in dell_columns

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
            # Possible columns that store hardware model information in different schemas
            if has('model'):
                select_cols.append('c.model')
            if has('product_model'):
                select_cols.append('c.product_model')
            if has('system_model'):
                select_cols.append('c.system_model')
            if has('modelo'):
                select_cols.append('c.modelo')
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
            # If the warranty table exists, include a few useful warranty columns
            if dell_columns:
                select_cols.append('dw.product_line_description as product_line_description')
                select_cols.append('dw.warranty_end_date as warranty_end_date')
                select_cols.append('dw.warranty_status as warranty_status')
            select_clause = ',\n            '.join(select_cols)

            base_query = f"""
            SELECT TOP 1000
            {select_clause}
            FROM computers c
            LEFT JOIN organizations o ON c.organization_id = o.id
            LEFT JOIN operating_systems os ON c.operating_system_id = os.id
            { 'LEFT JOIN dell_warranty dw ON c.id = dw.computer_id' if dell_columns else '' }
            WHERE c.is_domain_controller = 0
            """

            if inventory_filter == 'spare':
                query = base_query + " AND c.status = 'Spare' ORDER BY c.name"
            else:
                query = base_query + " ORDER BY c.name"

            try:
                rows = self.execute_query(query)
            except Exception:
                logger.exception('Primary computers query failed; falling back to minimal list')
                # Fallback: return a minimal list of computers (id, name)
                try:
                    rows = self.execute_query('SELECT id, name FROM computers ORDER BY name')
                    # normalize to expected structure
                    return [{'id': r.get('id'), 'name': r.get('name')} for r in rows]
                except Exception:
                    logger.exception('Fallback minimal computers query also failed')
                    return []
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
                            # Normalize model field from multiple possible column names
                            'model': (r.get('model') or r.get('product_model') or r.get('system_model') or r.get('modelo') or '') if any([has('model'), has('product_model'), has('system_model'), has('modelo')]) else '',
                        'usuarioAtual': r.get('usuario_atual') if has('usuario_atual') else '',
                        'usuarioAnterior': r.get('usuario_anterior') if has('usuario_anterior') else '',
                        'inventoryStatus': r.get('status') if has('status') else '',
                        'location': r.get('location') if has('location') else '',
                        'organizationName': r.get('organization_name') or '',
                        'organizationCode': r.get('organization_code') or ''
                        ,
                        # include warranty/product line fields if present
                        'product_line_description': r.get('product_line_description') if dell_columns else '',
                        'warranty_end_date': _format_dt(r.get('warranty_end_date')) if (dell_columns and r.get('warranty_end_date')) else None,
                        'warranty_status': r.get('warranty_status') if dell_columns else ''
                    })
                except Exception:
                    logger.exception('Error processing computer row')
                    continue
            return computers
        except Exception:
            logger.exception('get_computers_from_sql failed')
            return []

    def get_or_create_operating_system(self, os_name, os_version=None):
        """Mapeia sistema operacional do AD para ID da tabela operating_systems usando referência fixa"""
        if not os_name or os_name.strip() == '':
            return None
            
        try:
            # Normalizar nome do SO vindo do AD
            normalized_name = os_name.strip().lower()
            
            # Mapeamento baseado na tabela de referência fornecida
            os_mappings = {
                # Windows Desktop
                'windows 10 enterprise': 1,
                'windows 10 pro': 2,
                'windows 10 professional': 2,
                'windows 11 enterprise': 3, 
                'windows 11 pro': 4,
                'windows 11 professional': 4,
                'windows 7 professional': 11,  # Adicionar Windows 7 Professional
                'windows 7 ultimate': 11,
                'windows 8.1 pro': 16,
                'windows 10 enterprise 2016 ltsb': 15,
                'windows 11 pro for workstations': 17,
                
                # Windows Server
                'windows server 2019 standard': 5,
                'windows server 2022 standard': 6,
                'windows server 2022 datacenter': 7,
                'windows server 2012 r2 standard': 8,
                'windows server 2012 r2 datacenter': 9,
                'windows server 2008 r2 enterprise': 12,
                'windows server 2019 datacenter': 14,
                'windows storage server 2016 standard': 19,
                
                # Outros
                'windows rt': 10,
                'linux': 13,
                'unknown': 18,
                'pc-linux-gnu': 20
            }
            
            # Tentar match exato primeiro
            if normalized_name in os_mappings:
                os_id = os_mappings[normalized_name]
                logger.info(f"SO mapeado: '{os_name}' -> ID {os_id}")
                return os_id
            
            # Tentar match parcial
            for pattern, os_id in os_mappings.items():
                if pattern in normalized_name:
                    logger.info(f"SO mapeado (parcial): '{os_name}' -> ID {os_id} (pattern: {pattern})")
                    return os_id
            
            # Fallbacks baseados em palavras-chave
            if 'windows 11' in normalized_name:
                if 'enterprise' in normalized_name:
                    logger.info(f"SO mapeado (fallback): '{os_name}' -> Windows 11 Enterprise (ID 3)")
                    return 3  # Windows 11 Enterprise
                else:
                    logger.info(f"SO mapeado (fallback): '{os_name}' -> Windows 11 Pro (ID 4)")
                    return 4  # Windows 11 Pro
            elif 'windows 10' in normalized_name:
                if 'enterprise' in normalized_name:
                    logger.info(f"SO mapeado (fallback): '{os_name}' -> Windows 10 Enterprise (ID 1)")
                    return 1  # Windows 10 Enterprise
                else:
                    logger.info(f"SO mapeado (fallback): '{os_name}' -> Windows 10 Pro (ID 2)")
                    return 2  # Windows 10 Pro
            elif 'server 2019' in normalized_name:
                if 'datacenter' in normalized_name:
                    logger.info(f"SO mapeado (fallback): '{os_name}' -> Server 2019 Datacenter (ID 14)")
                    return 14  # Windows Server 2019 Datacenter
                else:
                    logger.info(f"SO mapeado (fallback): '{os_name}' -> Server 2019 Standard (ID 5)")
                    return 5   # Windows Server 2019 Standard
            elif 'server 2022' in normalized_name:
                if 'datacenter' in normalized_name:
                    logger.info(f"SO mapeado (fallback): '{os_name}' -> Server 2022 Datacenter (ID 7)")
                    return 7   # Windows Server 2022 Datacenter
                else:
                    logger.info(f"SO mapeado (fallback): '{os_name}' -> Server 2022 Standard (ID 6)")
                    return 6   # Windows Server 2022 Standard
            elif 'server 2012' in normalized_name:
                if 'datacenter' in normalized_name:
                    logger.info(f"SO mapeado (fallback): '{os_name}' -> Server 2012 R2 Datacenter (ID 9)")
                    return 9   # Windows Server 2012 R2 Datacenter
                else:
                    logger.info(f"SO mapeado (fallback): '{os_name}' -> Server 2012 R2 Standard (ID 8)")
                    return 8   # Windows Server 2012 R2 Standard
            elif 'linux' in normalized_name:
                logger.info(f"SO mapeado (fallback): '{os_name}' -> Linux (ID 20)")
                return 20  # pc-linux-gnu ou Linux genérico
            
            # Se não encontrou correspondência, usar "unknown"
            logger.warning(f"SO não mapeado: '{os_name}', usando 'unknown' (ID 18)")
            return 18  # unknown
            
        except Exception as e:
            logger.error(f"Erro ao mapear SO '{os_name}': {e}")
            return 18  # unknown como fallback
            family = 'Server' if is_server else ('Linux' if 'linux' in normalized_name.lower() else 'Windows')
            
            insert_query = """
                INSERT INTO operating_systems (name, version, architecture, family, is_server, created_at)
                VALUES (?, ?, 'x64', ?, ?, GETDATE())
            """
            
            self.execute_query(insert_query, [normalized_name, os_version, family, is_server], fetch=False)
            
            # Buscar o ID criado
            result = self.execute_query(query, [normalized_name])
            if result:
                logger.info(f"Criado novo SO: {normalized_name} (ID: {result[0]['id']})")
                return result[0]['id']
                
        except Exception as e:
            logger.error(f"Erro ao criar/buscar SO '{normalized_name}': {e}")
            
        return None

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
            # Handle both naming conventions: AD Manager output (camelCase) and raw AD data
            dns_hostname = computer_data.get('dNSHostName') or computer_data.get('dnsHostName') or computer_data.get('dns_hostname') or ''
            distinguished_name = computer_data.get('distinguishedName') or computer_data.get('dn') or computer_data.get('distinguished_name') or ''
            description = computer_data.get('description', '')
            is_enabled = bool(computer_data.get('userAccountControl', 0) & 0x0002 == 0)  # ACCOUNTDISABLE flag
            # If AD Manager already computed 'disabled', use it as fallback
            if 'disabled' in computer_data and 'userAccountControl' not in computer_data:
                is_enabled = not computer_data.get('disabled', False)
            user_account_control = computer_data.get('userAccountControl') or computer_data.get('user_account_control') or 0
            primary_group_id = computer_data.get('primaryGroupID') or computer_data.get('primary_group_id') or 515
            sam_account_name = computer_data.get('sAMAccountName') or computer_data.get('sam_account_name') or name
            
            # Processar timestamps — handle both raw AD field names and AD Manager normalized names
            last_logon = computer_data.get('lastLogonTimestamp') or computer_data.get('lastLogon') or computer_data.get('last_logon_timestamp')
            created_date = computer_data.get('whenCreated') or computer_data.get('created') or computer_data.get('created_date')
            
            # Buscar ou criar sistema operacional
            operating_system_id = None
            os_name = computer_data.get('os')  # Campo correto do AD
            os_version = computer_data.get('osVersion')  # Campo correto do AD
            
            if os_name:
                operating_system_id = self.get_or_create_operating_system(
                    os_name,
                    os_version
                )
            
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
                    operating_system_id = ?,
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
                    operating_system_id,
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
                    created_date, operating_system_id, last_sync_ad, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE(), GETDATE())
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
                    created_date,
                    operating_system_id
                ]
                
                self.execute_query(insert_query, params, fetch=False)
                
                # Buscar o ID do registro inserido
                new_record = self.execute_query("SELECT id FROM computers WHERE name = ?", [name])
                return new_record[0]['id'] if new_record else None  # Retorna None (nova inserção)
                
        except Exception as e:
            logger.exception(f'Erro ao sincronizar computador {computer_data.get("name", "unknown")}: {e}')
            return None

    def update_os_for_computer(self, computer_id, os_name, os_version=None):
        """Update operating_system_id for a single computer given its OS name from AD.
        
        This is called after warranty updates or individual syncs to ensure OS is always saved.
        """
        if not os_name or not computer_id:
            return False
        try:
            operating_system_id = self.get_or_create_operating_system(os_name, os_version)
            if operating_system_id:
                self.execute_query(
                    "UPDATE computers SET operating_system_id = ? WHERE id = ? AND (operating_system_id IS NULL OR operating_system_id != ?)",
                    params=[operating_system_id, computer_id, operating_system_id],
                    fetch=False
                )
                return True
        except Exception:
            logger.exception(f'update_os_for_computer failed for computer_id={computer_id}')
        return False

    def update_os_for_computer_by_name(self, computer_name):
        """Resolve OS from AD data and update operating_system_id in SQL for a single computer.
        
        Used after warranty updates to keep OS in sync.
        """
        if not computer_name:
            return False
        try:
            # Import AD manager lazily to avoid circular imports
            from . import ad_manager
            all_computers = ad_manager.get_computers()
            ad_computer = next((c for c in all_computers if c.get('name') == computer_name), None)
            if not ad_computer:
                return False
            
            os_name = ad_computer.get('os')
            os_version = ad_computer.get('osVersion')
            if not os_name or os_name == 'N/A':
                return False
            
            # Get computer ID from SQL  
            rows = self.execute_query("SELECT id FROM computers WHERE name = ?", params=[computer_name])
            if not rows:
                return False
            computer_id = rows[0]['id']
            
            return self.update_os_for_computer(computer_id, os_name, os_version)
        except Exception:
            logger.exception(f'update_os_for_computer_by_name failed for {computer_name}')
            return False

    def update_last_logon(self, computer_name, last_logon_iso):
        """Update last_logon_timestamp in SQL for a single computer.
        
        Only updates if the new value is more recent than the stored value.
        """
        if not computer_name or not last_logon_iso:
            return False
        try:
            self.execute_query(
                """UPDATE computers 
                   SET last_logon_timestamp = ?
                   WHERE name = ? 
                     AND (last_logon_timestamp IS NULL OR last_logon_timestamp < ?)""",
                params=[last_logon_iso, computer_name, last_logon_iso],
                fetch=False
            )
            return True
        except Exception:
            logger.exception(f'update_last_logon failed for {computer_name}')
            return False

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

    def save_warranty_to_database(self, computer_id_or_service_tag, warranty_data):
        """Save warranty information to database.

        Accepts either an integer `computer_id` or a service-tag string. If a
        service-tag is provided the method will try to resolve the matching
        computer id in `computers`. This prevents attempts to insert a
        non-integer into the `computer_id` FK column.
        """
        try:
            # Normalize: if a non-int service tag was passed, try to resolve it
            computer_id = None
            try:
                # if caller passed an int-like value, keep it
                if isinstance(computer_id_or_service_tag, int):
                    computer_id = computer_id_or_service_tag
                else:
                    # try convert if passed numeric string
                    try:
                        computer_id = int(computer_id_or_service_tag)
                    except Exception:
                        # treat as service_tag string and attempt lookup
                        service_tag = str(computer_id_or_service_tag).strip()
                        if service_tag:
                            # try exact match on computer name, then contains
                            rows = self.execute_query("SELECT TOP 1 id FROM computers WHERE UPPER(name) = UPPER(?)", params=(service_tag,))
                            if rows:
                                computer_id = rows[0].get('id')
                            else:
                                rows = self.execute_query("SELECT TOP 1 id FROM computers WHERE UPPER(name) LIKE UPPER(?)", params=(f"%{service_tag}%",))
                                if rows:
                                    computer_id = rows[0].get('id')

            except Exception:
                computer_id = None

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

                # Helper to check existence of a row by computer_id (only if we have a numeric id)
                row_exists = False
                if computer_id is not None and _has('computer_id'):
                    try:
                        cursor.execute("SELECT id FROM dell_warranty WHERE computer_id = ?", (computer_id,))
                        row_exists = cursor.fetchone() is not None
                    except Exception:
                        logger.exception('Failed to check existing dell_warranty row')
                        row_exists = False

                if warranty_data.get('success'):
                    # Para casos de sucesso, service_tag é obrigatório
                    service_tag = warranty_data.get('service_tag')
                    if not service_tag or service_tag.strip() == '':
                        logger.warning(f'Cannot save warranty data without valid service_tag for computer_id {computer_id}')
                        return True  # Retorna True para não causar erro, mas não insere
                    
                    # Build a map of candidate columns -> values
                    candidates = {
                        'service_tag': service_tag,
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

                        # ensure we don't try to insert a non-int computer_id into an int column
                        if 'computer_id' in insert_cols and computer_id is None:
                            insert_cols.remove('computer_id')
                            insert_vals = [v for i, v in enumerate(insert_vals) if insert_cols and i < len(insert_vals)]

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
                    elif not row_exists:
                        # Para inserir erro quando não existe registro, precisamos de service_tag
                        # Usar 'UNKNOWN' como valor padrão para service_tag em casos de erro
                        if _has('computer_id') and _has('service_tag') and _has('last_error'):
                            insert_cols = ['computer_id', 'service_tag', 'last_updated', 'cache_expires_at', 'last_error']
                            error_service_tag = warranty_data.get('service_tag') or 'UNKNOWN'
                            params = (computer_id, error_service_tag, datetime.now(), retry_time, f"{warranty_data.get('code', 'ERROR')}: {warranty_data.get('error', 'Unknown error')}")
                            placeholders = ', '.join(['?'] * len(insert_cols))
                            insert_query = f"INSERT INTO dell_warranty ({', '.join(insert_cols)}) VALUES ({placeholders})"
                            cursor.execute(insert_query, params)
                        else:
                            # Se não podemos inserir erro devido à falta de colunas necessárias, apenas log
                            logger.warning('Cannot record warranty error due to missing required columns for computer_id %s', computer_id)
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
