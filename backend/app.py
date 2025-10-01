from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from datetime import datetime, timedelta, timezone

from ldap3 import Server, Connection, ALL, SUBTREE, MODIFY_REPLACE
import json
import os
import pyodbc
import threading
import time
from dotenv import load_dotenv
import subprocess
import re

import logging
import pypsrp
import traceback
# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

app = Flask(__name__)

# Configuração CORS mais robusta e permissiva para debugging
CORS(app, 
     resources={
         r"/api/*": {
             "origins": "*",  # Temporariamente permitir todas as origens para debug
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
             "allow_headers": ["Content-Type", "Authorization", "Accept", "X-Requested-With", "Origin"],
             "supports_credentials": False,
             "send_wildcard": True,
             "max_age": 86400  # Cache preflight por 24h
         }
     })

# Configurações do Active Directory
AD_SERVER = os.getenv('AD_SERVER', 'ldap://CLODC02.snm.local')
AD_USERNAME = os.getenv('AD_USERNAME', 'SNM\\adm.itservices')
AD_PASSWORD = os.getenv('AD_PASSWORD', 'xmZ7P@5vkKzg')
AD_BASE_DN = os.getenv('AD_BASE_DN', 'DC=snm,DC=local')

# Configurações Dell Warranty API
DELL_CLIENT_ID = os.getenv('DELL_CLIENT_ID', 'l75c9d200744a444a08c54b666ddbd9b1a')
DELL_CLIENT_SECRET = os.getenv('DELL_CLIENT_SECRET', '5a6bfc5dd76c40a6bd8b896c6ab63e9e')

# Configurações SQL Server
SQL_SERVER = os.getenv('SQL_SERVER', 'CLOSQL02')
SQL_DATABASE = os.getenv('SQL_DATABASE', 'DellReports')
SQL_USERNAME = os.getenv('SQL_USERNAME')
SQL_PASSWORD = os.getenv('SQL_PASSWORD')
USE_WINDOWS_AUTH = os.getenv('USE_WINDOWS_AUTH', 'true').lower() == 'true'

class SQLManager:
    def __init__(self):
        self.connection_string = self._build_connection_string()
        self._test_connection()
    
    def _build_connection_string(self):
        """Constrói string de conexão para SQL Server"""
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
    
    def _test_connection(self):
        """Testa conexão com SQL Server"""
        try:
            with pyodbc.connect(self.connection_string) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                print(f"✅ Conexão SQL Server estabelecida: {SQL_SERVER}/{SQL_DATABASE}")
        except Exception as e:
            print(f"❌ Erro na conexão SQL Server: {e}")
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
            print(f"❌ Erro SQL: {e}")
            raise
    
    def get_computers_from_sql(self):
        """Busca computadores do SQL Server"""
        query = """
        SELECT 
            c.id,
            c.name,
            c.dns_hostname,
            c.distinguished_name as dn,
            c.is_enabled,
            c.is_domain_controller,
            c.description,
            c.last_logon_timestamp as lastLogon,
            c.created_date as created,
            c.user_account_control,
            c.primary_group_id,
            c.last_sync_ad,
            c.ip_address,
            c.mac_address,
            
            -- Organização
            o.name as organization_name,
            o.code as organization_code,
            
            -- Sistema Operacional
            os.name as os,
            os.version as osVersion,
            os.family as os_family,
            
            -- Status calculado
            CASE 
                WHEN c.last_logon_timestamp IS NULL THEN 'never'
                WHEN c.last_logon_timestamp > DATEADD(day, -7, GETDATE()) THEN 'recent'
                WHEN c.last_logon_timestamp > DATEADD(day, -30, GETDATE()) THEN 'moderate'
                ELSE 'old'
            END as login_status,
            
            DATEDIFF(day, c.last_logon_timestamp, GETDATE()) as days_since_last_logon
            
        FROM computers c
        LEFT JOIN organizations o ON c.organization_id = o.id
        LEFT JOIN operating_systems os ON c.operating_system_id = os.id
        WHERE c.is_domain_controller = 0
        ORDER BY c.name
        """
        
        try:
            print(f"🔍 Executando query SQL para buscar computadores...")
            results = self.execute_query(query)
            print(f"📊 SQL retornou {len(results)} registros")
            
            if not results:
                print("⚠️  Nenhum computador encontrado no SQL - tabela pode estar vazia")
                return []
            
            computers = []
            for row in results:
                try:
                    computer = {
                        'id': row['id'],
                        'name': row['name'],
                        'dn': row['dn'],
                        'lastLogon': row['lastLogon'].isoformat() if row['lastLogon'] else None,
                        'os': row['os'] or 'N/A',
                        'osVersion': row['osVersion'] or 'N/A', 
                        'created': row['created'].isoformat() if row['created'] else None,
                        'description': row['description'] or '',
                        'disabled': not row['is_enabled'],
                        'userAccountControl': row['user_account_control'] or 0,
                        'primaryGroupID': row['primary_group_id'] or 515,
                        'dnsHostName': row['dns_hostname'] or '',
                        'ipAddress': row['ip_address'] or '',
                        'macAddress': row['mac_address'] or '',
                        'organizationName': row['organization_name'] or '',
                        'organizationCode': row['organization_code'] or '',
                        'loginStatus': row['login_status'],
                        'daysSinceLastLogon': row['days_since_last_logon'],
                        'lastSyncAd': row['last_sync_ad'].isoformat() if row['last_sync_ad'] else None
                    }
                    computers.append(computer)
                except Exception as row_error:
                    print(f"❌ Erro ao processar linha: {row_error}")
                    continue
            
            print(f"✅ Processados {len(computers)} computadores com sucesso")
            return computers
            
        except Exception as e:
            print(f"❌ Erro ao buscar computadores do SQL: {e}")
            print(f"❌ Detalhes do erro: {type(e).__name__}")
            return []
    
    def sync_computer_to_sql(self, computer_data):
        """Sincroniza um computador do AD para o SQL"""
        try:
            org_code = self._extract_organization_code(computer_data['name'])
            
            query = """
            EXEC SyncComputerFromAD 
                @p_name = ?,
                @p_dns_hostname = ?,
                @p_distinguished_name = ?,
                @p_is_enabled = ?,
                @p_user_account_control = ?,
                @p_primary_group_id = ?,
                @p_description = ?,
                @p_last_logon_timestamp = ?,
                @p_created_date = ?,
                @p_organization_code = ?,
                @p_os_name = ?
            """
            
            params = (
                computer_data['name'],
                computer_data.get('dnsHostName', ''),
                computer_data['dn'],
                not computer_data.get('disabled', False),
                computer_data.get('userAccountControl', 0),
                computer_data.get('primaryGroupID', 515),
                computer_data.get('description', ''),
                self._parse_datetime(computer_data.get('lastLogon')),
                self._parse_datetime(computer_data.get('created')),
                org_code,
                computer_data.get('os', 'N/A')
            )
            
            result = self.execute_query(query, params, fetch=True)
            if result:
                return result[0]['computer_id']
            return None
            
        except Exception as e:
            print(f"❌ Erro ao sincronizar computador {computer_data.get('name', 'Unknown')}: {e}")
            return None
    
    def _extract_organization_code(self, computer_name):
        """Extrai código da organização do nome do computador"""
        name_upper = computer_name.upper()
        
        org_mapping = {
            'SHQ': 'SHQ', 'CLO': 'SHQ',
            'DIA': 'DIA',
            'TOP': 'TOP',
            'RUB': 'RUB',
            'ESM': 'ESM',
            'ONI': 'ONI',
            'JAD': 'JAD'
        }
        
        for prefix, code in org_mapping.items():
            if name_upper.startswith(prefix):
                return code
        
        return 'SHQ'
    
    def _parse_datetime(self, date_string):
        """Converte string de data para datetime"""
        if not date_string:
            return None
        
        try:
            if isinstance(date_string, str):
                return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            return date_string
        except:
            return None
    
    def log_sync_operation(self, sync_type, status, stats=None, error_message=None):
        """Registra operação de sincronização"""
        try:
            query = """
            INSERT INTO sync_logs (
                sync_type, start_time, end_time, status,
                computers_found, computers_added, computers_updated, 
                errors_count, error_message, triggered_by
            ) VALUES (?, GETDATE(), GETDATE(), ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                sync_type,
                status,
                stats.get('found', 0) if stats else 0,
                stats.get('added', 0) if stats else 0,
                stats.get('updated', 0) if stats else 0,
                stats.get('errors', 0) if stats else 0,
                error_message,
                'api_sync'
            )
            
            self.execute_query(query, params, fetch=False)
            
        except Exception as e:
            print(f"❌ Erro ao registrar log de sync: {e}")

    def update_computer_status_in_sql(self, computer_name, is_enabled, user_account_control=None):
        """Atualiza status do computador no cache SQL"""
        try:
            query = """
            UPDATE computers 
            SET 
                is_enabled = ?,
                user_account_control = COALESCE(?, user_account_control),
                last_modified = GETDATE(),
                modified_by = 'API-ToggleStatus'
            WHERE name = ?
            """
            
            params = (is_enabled, user_account_control, computer_name)
            rows_affected = self.execute_query(query, params, fetch=False)
            
            logger.info(f"📊 Status atualizado no SQL para {computer_name}. Linhas afetadas: {rows_affected}")
            return rows_affected > 0
            
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar SQL para {computer_name}: {e}")
            return False

    def log_computer_operation(self, computer_name, operation, status, details=None, error_message=None):
        """Registra operação realizada no computador"""
        try:
            query = """
            INSERT INTO computer_operations_log (
                computer_name, operation, status, operation_time,
                details, error_message, user_context
            ) VALUES (?, ?, ?, GETDATE(), ?, ?, ?)
            """
            
            params = (
                computer_name,
                operation,
                status,
                details,
                error_message,
                'api_user'
            )
            
            self.execute_query(query, params, fetch=False)
            
        except Exception as e:
            logger.error(f"❌ Erro ao registrar log de operação: {e}")

class ADManager:
    def __init__(self):
        self.server = Server(AD_SERVER, get_info=ALL)
        self.connection = None
        
    def connect(self):
        try:
            self.connection = Connection(
                self.server,
                user=AD_USERNAME,
                password=AD_PASSWORD,
                auto_bind=True
            )
            return True
        except Exception as e:
            print(f"❌ Erro ao conectar no AD: {e}")
            return False
    
    def get_computers(self):
        """Busca computadores do AD (para sincronização)"""
        if not self.connect():
            return []
        
        try:
            search_filter = '''(&
                (objectClass=computer)
                (!(primaryGroupID=516))
                (!(userAccountControl:1.2.840.113556.1.4.803:=8192))
            )'''
            
            search_filter = ''.join(search_filter.split())
            
            attributes = [
                'cn', 'distinguishedName', 'lastLogonTimestamp', 
                'operatingSystem', 'operatingSystemVersion', 
                'whenCreated', 'description', 'userAccountControl',
                'primaryGroupID', 'servicePrincipalName', 'dNSHostName'
            ]
            
            self.connection.search(
                search_base=AD_BASE_DN,
                search_filter=search_filter,
                search_scope=SUBTREE,
                attributes=attributes,
                paged_size=1000
            )
            
            computers = []
            excluded_count = 0
            
            for entry in self.connection.entries:
                computer_name = str(entry.cn).upper()
                
                dc_indicators = ['DC0', 'DC1', 'DC2', 'DOMAIN-CONTROLLER', 'PDC', 'BDC', 'ADDC']
                if any(indicator in computer_name for indicator in dc_indicators):
                    excluded_count += 1
                    continue
                
                os_name = str(entry.operatingSystem) if entry.operatingSystem else ''
                if 'Server' in os_name:
                    spns = entry.servicePrincipalName.values if entry.servicePrincipalName else []
                    dc_spns = ['ldap/', 'gc/', 'E3514235-4B06-11D1-AB04-00C04FC2DCD2/']
                    if any(any(dc_spn in str(spn) for dc_spn in dc_spns) for spn in spns):
                        excluded_count += 1
                        continue
                
                uac = int(entry.userAccountControl.value) if entry.userAccountControl.value else 0
                is_disabled = bool(uac & 2)
                
                last_logon = None
                if entry.lastLogonTimestamp.value:
                    last_logon = entry.lastLogonTimestamp.value.isoformat()
                
                computers.append({
                    'name': str(entry.cn),
                    'dn': str(entry.distinguishedName),
                    'lastLogon': last_logon,
                    'os': str(entry.operatingSystem) if entry.operatingSystem else 'N/A',
                    'osVersion': str(entry.operatingSystemVersion) if entry.operatingSystemVersion else 'N/A',
                    'created': entry.whenCreated.value.isoformat() if entry.whenCreated.value else None,
                    'description': str(entry.description) if entry.description else '',
                    'disabled': is_disabled,
                    'userAccountControl': uac,
                    'primaryGroupID': int(entry.primaryGroupID.value) if entry.primaryGroupID.value else 515,
                    'dnsHostName': str(entry.dNSHostName) if entry.dNSHostName else ''
                })
            
            print(f"📊 AD: {len(computers)} computadores, {excluded_count} DCs excluídos")
            return computers
            
        except Exception as e:
            print(f"❌ Erro ao buscar computadores do AD: {e}")
            return []
        finally:
            if self.connection:
                self.connection.unbind()

class ADComputerManager:
    """Classe para gerenciar operações de toggle em computadores do Active Directory"""
    
    def __init__(self):
        self.server = Server(AD_SERVER, get_info=ALL)
        self.connection = None
        
    def connect(self):
        """Conecta ao Active Directory"""
        try:
            self.connection = Connection(
                self.server,
                user=AD_USERNAME,
                password=AD_PASSWORD,
                auto_bind=True
            )
            logger.info(f"✅ Conectado ao AD: {AD_SERVER}")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao conectar no AD: {e}")
            return False
    
    def disconnect(self):
        """Desconecta do Active Directory"""
        if self.connection:
            self.connection.unbind()
            self.connection = None
    
    def find_computer(self, computer_name):
        """Busca computador no AD por nome"""
        if not self.connect():
            raise Exception("Falha na conexão com Active Directory")
        
        try:
            search_filter = f"(&(objectClass=computer)(|(cn={computer_name})(sAMAccountName={computer_name}$)))"
            
            self.connection.search(
                search_base=AD_BASE_DN,
                search_filter=search_filter,
                search_scope=SUBTREE,
                attributes=['cn', 'distinguishedName', 'userAccountControl', 'description', 'operatingSystem']
            )
            
            if not self.connection.entries:
                raise Exception(f"Computador '{computer_name}' não encontrado no Active Directory")
            
            computer = self.connection.entries[0]
            
            dn = str(computer.distinguishedName)
            uac = int(computer.userAccountControl.value) if computer.userAccountControl.value else 0
            is_disabled = bool(uac & 2)
            
            logger.info(f"🔍 Computador encontrado: {computer_name} (UAC: {uac}, Disabled: {is_disabled})")
            
            return {
                'name': str(computer.cn),
                'dn': dn,
                'userAccountControl': uac,
                'disabled': is_disabled,
                'description': str(computer.description) if computer.description else '',
                'operatingSystem': str(computer.operatingSystem) if computer.operatingSystem else ''
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar computador {computer_name}: {e}")
            raise
        finally:
            self.disconnect()
    
    def toggle_computer_status(self, computer_name, action):
        """
        Ativa ou desativa computador no AD
        action: 'enable' ou 'disable'
        """
        if action not in ['enable', 'disable']:
            raise ValueError("Ação deve ser 'enable' ou 'disable'")
        
        if not self.connect():
            raise Exception("Falha na conexão com Active Directory")
        
        try:
            computer = self.find_computer(computer_name)
            current_uac = computer['userAccountControl']
            is_currently_disabled = computer['disabled']
            
            if action == 'disable' and is_currently_disabled:
                return {
                    'success': True,
                    'message': f'Computador {computer_name} já está desativado',
                    'already_in_desired_state': True,
                    'current_status': {
                        'disabled': is_currently_disabled,
                        'userAccountControl': current_uac
                    }
                }
            
            if action == 'enable' and not is_currently_disabled:
                return {
                    'success': True,
                    'message': f'Computador {computer_name} já está ativado',
                    'already_in_desired_state': True,
                    'current_status': {
                        'disabled': is_currently_disabled,
                        'userAccountControl': current_uac
                    }
                }
            
            if action == 'disable':
                new_uac = current_uac | 2
            else:
                new_uac = current_uac & ~2
            
            logger.info(f"🔄 Modificando UAC de {current_uac} para {new_uac}")
            
            if not self.connect():
                raise Exception("Falha na reconexão com Active Directory")
            
            modify_success = self.connection.modify(
                computer['dn'],
                {'userAccountControl': [(MODIFY_REPLACE, [str(new_uac)])]}
            )
            
            if not modify_success:
                error_info = self.connection.result
                raise Exception(f"Falha na modificação do AD: {error_info.get('description', 'Erro desconhecido')}")
            
            action_text = 'desativado' if action == 'disable' else 'ativado'
            logger.info(f"✅ Computador {computer_name} {action_text} com sucesso")
            
            return {
                'success': True,
                'message': f'Computador {computer_name} {action_text} com sucesso',
                'operation': {
                    'computer_name': computer_name,
                    'action': action,
                    'previous_status': {
                        'disabled': is_currently_disabled,
                        'userAccountControl': current_uac
                    },
                    'new_status': {
                        'disabled': action == 'disable',
                        'userAccountControl': new_uac
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao {action} computador {computer_name}: {e}")
            raise
        finally:
            self.disconnect()
    
    def toggle_computer_status_powershell(self, computer_name, action):
        """Fallback usando PowerShell para ativar/desativar computador"""
        try:
            if action == 'enable':
                ps_command = f"Enable-ADAccount -Identity '{computer_name}$'"
                action_text = 'ativado'
            else:
                ps_command = f"Disable-ADAccount -Identity '{computer_name}$'"
                action_text = 'desativado'
            
            full_command = [
                'powershell.exe',
                '-ExecutionPolicy', 'Bypass',
                '-Command',
                f"""
                try {{
                    Import-Module ActiveDirectory -ErrorAction Stop
                    {ps_command}
                    $computer = Get-ADComputer -Identity '{computer_name}' -Properties Enabled, userAccountControl
                    Write-Output "SUCCESS: Computador {action_text}. Enabled: $($computer.Enabled), UAC: $($computer.userAccountControl)"
                }} catch {{
                    Write-Output "ERROR: $($_.Exception.Message)"
                }}
                """
            ]
            
            logger.info(f"🔄 Executando PowerShell para {action} {computer_name}")
            
            result = subprocess.run(
                full_command,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            output = result.stdout.strip()
            error_output = result.stderr.strip()
            
            logger.info(f"PowerShell output: {output}")
            if error_output:
                logger.warning(f"PowerShell stderr: {error_output}")
            
            if result.returncode == 0 and "SUCCESS:" in output:
                return {
                    'success': True,
                    'message': f'Computador {computer_name} {action_text} com sucesso (PowerShell)',
                    'method': 'powershell',
                    'output': output
                }
            else:
                error_msg = output if "ERROR:" in output else error_output
                raise Exception(f"PowerShell falhou: {error_msg}")
                
        except subprocess.TimeoutExpired:
            raise Exception("Timeout na execução do PowerShell")
        except Exception as e:
            logger.error(f"❌ Erro no PowerShell para {computer_name}: {e}")
            raise

class DellWarrantyAPI:
    def __init__(self):
        self.base_url = "https://apigtwb2c.us.dell.com"
        self.token = None
        self.token_expires_at = None
        
    def get_access_token(self):
        try:
            url = f"{self.base_url}/auth/oauth/v2/token"
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            data = {
                'grant_type': 'client_credentials',
                'client_id': DELL_CLIENT_ID,
                'client_secret': DELL_CLIENT_SECRET
            }
            
            response = requests.post(url, headers=headers, data=data, timeout=30)
            
            if response.status_code == 200:
                token_data = response.json()
                self.token = token_data.get('access_token')
                expires_in = token_data.get('expires_in', 3600)
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)
                return True
            else:
                print(f"❌ Erro na autenticação Dell: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao obter token Dell: {e}")
            return False
    
    def is_token_valid(self):
        return (self.token and 
                self.token_expires_at and 
                datetime.now() < self.token_expires_at)
    
    def ensure_valid_token(self):
        if not self.is_token_valid():
            return self.get_access_token()
        return True
    
    def get_warranty_info(self, service_tag):
        if not service_tag or len(service_tag.strip()) < 5:
            return {'error': 'Service tag inválido', 'code': 'INVALID_SERVICE_TAG'}
        
        service_tag = service_tag.strip().upper()
        original_service_tag = service_tag
        
        prefixes_to_remove = ['SHQ', 'DIA', 'TOP', 'RUB', 'ESM', 'ONI', 'JAD']
        for prefix in prefixes_to_remove:
            if service_tag.startswith(prefix):
                service_tag = service_tag[len(prefix):]
                break
        
        if len(service_tag) < 5:
            return {'error': 'Service tag inválido após remoção do prefixo', 'code': 'INVALID_SERVICE_TAG'}
        
        if not self.ensure_valid_token():
            return {'error': 'Erro de autenticação com Dell API', 'code': 'AUTH_ERROR'}
        
        try:
            url = f"{self.base_url}/PROD/sbil/eapi/v5/asset-entitlements"
            headers = {
                'Authorization': f'Bearer {self.token}',
                'Accept': 'application/json'
            }
            params = {'servicetags': service_tag}
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if not data or len(data) == 0:
                    return {'error': 'Service tag não encontrado', 'code': 'SERVICE_TAG_NOT_FOUND'}
                
                warranty_data = data[0]
                
                if warranty_data.get('invalid', False):
                    return {
                        'error': 'Service tag inválido',
                        'code': 'INVALID_SERVICE_TAG',
                        'serviceTag': original_service_tag
                    }
                
                modelo = warranty_data.get('productLineDescription', 'Não especificado')
                entitlements = warranty_data.get('entitlements', [])
                
                if not entitlements:
                    return {
                        'serviceTag': original_service_tag,
                        'serviceTagLimpo': warranty_data.get('serviceTag', service_tag),
                        'modelo': modelo,
                        'dataExpiracao': 'Sem garantia',
                        'status': 'Sem garantia',
                        'entitlements': [],
                        'shipDate': warranty_data.get('shipDate'),
                        'orderNumber': warranty_data.get('orderNumber')
                    }
                
                latest_end_date = None
                valid_entitlements = []
                
                for entitlement in entitlements:
                    valid_entitlements.append({
                        'serviceLevelDescription': entitlement.get('serviceLevelDescription', 'N/A'),
                        'serviceLevelCode': entitlement.get('serviceLevelCode', 'N/A'),
                        'startDate': entitlement.get('startDate'),
                        'endDate': entitlement.get('endDate'),
                        'entitlementType': entitlement.get('entitlementType', 'N/A'),
                        'itemNumber': entitlement.get('itemNumber', 'N/A')
                    })
                    
                    if entitlement.get('endDate'):
                        try:
                            end_date = datetime.fromisoformat(entitlement.get('endDate').replace('Z', '+00:00'))
                            if latest_end_date is None or end_date > latest_end_date:
                                latest_end_date = end_date
                        except Exception as e:
                            continue
                
                if latest_end_date:
                    now = datetime.now(timezone.utc)
                    status = "Em garantia" if latest_end_date > now else "Expirado"
                    data_expiracao = latest_end_date.strftime('%d/%m/%Y')
                    
                    return {
                        'serviceTag': original_service_tag,
                        'serviceTagLimpo': warranty_data.get('serviceTag', service_tag),
                        'modelo': modelo,
                        'dataExpiracao': data_expiracao,
                        'status': status,
                        'entitlements': valid_entitlements,
                        'dataSource': 'entitlements'
                    }
                else:
                    return {
                        'serviceTag': original_service_tag,
                        'serviceTagLimpo': warranty_data.get('serviceTag', service_tag),
                        'modelo': modelo,
                        'dataExpiracao': 'Não disponível',
                        'status': 'Data de expiração desconhecida',
                        'entitlements': valid_entitlements,
                        'shipDate': warranty_data.get('shipDate'),
                        'orderNumber': warranty_data.get('orderNumber')
                    }
                
            elif response.status_code == 401:
                if self.get_access_token():
                    return self.get_warranty_info(service_tag)
                return {'error': 'Erro de autenticação', 'code': 'AUTH_ERROR'}
                
            elif response.status_code == 404:
                return {'error': 'Service tag não encontrado', 'code': 'SERVICE_TAG_NOT_FOUND'}
                
            else:
                return {'error': f'Erro interno da API Dell (HTTP {response.status_code})', 'code': 'DELL_API_ERROR'}
                
        except requests.exceptions.Timeout:
            return {'error': 'Timeout na conexão com Dell API', 'code': 'TIMEOUT_ERROR'}
        except Exception as e:
            print(f"❌ Erro inesperado ao consultar garantia Dell: {e}")
            return {'error': 'Erro interno do servidor', 'code': 'INTERNAL_ERROR'}

    def get_warranty_info_bulk(self, service_tags):
        """
        Consulta múltiplas service tags de uma única vez (lista de service_tags)
        A API Dell aceita até 100 service tags separadas por vírgula.
        Retorna um dict mapeando cada service tag limpa para o resultado correspondente (mesmo formato de get_warranty_info)
        """
        if not isinstance(service_tags, (list, tuple)):
            return {'error': 'service_tags deve ser uma lista'}

        # Preparar lista com limites
        cleaned_tags = [t.strip().upper() for t in service_tags if t and isinstance(t, str)]
        if not cleaned_tags:
            return {}

        results_map = {}

        # Processar em batches de 100
        batch_size = 100
        for i in range(0, len(cleaned_tags), batch_size):
            batch = cleaned_tags[i:i+batch_size]

            # Remover prefixes como feito na get_warranty_info? A Dell aceita tags com ou sem prefixo,
            # mas para consistência vamos enviar tags limpas (sem prefixos SHQ/ESM/etc) quando detectados.
            batch_to_send = []
            for tag in batch:
                t = tag
                for prefix in ['SHQ', 'DIA', 'TOP', 'RUB', 'ESM', 'ONI', 'JAD', 'CLO']:
                    if t.startswith(prefix) and len(t) > len(prefix):
                        t = t[len(prefix):]
                        break
                batch_to_send.append(t)

            # Garantir token
            if not self.ensure_valid_token():
                return {'error': 'Erro de autenticação com Dell API', 'code': 'AUTH_ERROR'}

            try:
                url = f"{self.base_url}/PROD/sbil/eapi/v5/asset-entitlements"
                headers = {
                    'Authorization': f'Bearer {self.token}',
                    'Accept': 'application/json'
                }
                params = {'servicetags': ','.join(batch_to_send)}

                response = requests.get(url, headers=headers, params=params, timeout=60)

                if response.status_code == 200:
                    data = response.json()
                    # data é uma lista com resultados correspondentes
                    for warranty_data in data:
                        st = warranty_data.get('serviceTag') or ''
                        # Mapear para o formato similar ao get_warranty_info
                        if warranty_data.get('invalid', False):
                            results_map[st] = {'error': 'Service tag inválido', 'code': 'INVALID_SERVICE_TAG', 'serviceTag': st}
                            continue

                        modelo = warranty_data.get('productLineDescription', 'Não especificado')
                        entitlements = warranty_data.get('entitlements', [])

                        latest_end_date = None
                        valid_entitlements = []
                        for entitlement in entitlements:
                            valid_entitlements.append({
                                'serviceLevelDescription': entitlement.get('serviceLevelDescription', 'N/A'),
                                'serviceLevelCode': entitlement.get('serviceLevelCode', 'N/A'),
                                'startDate': entitlement.get('startDate'),
                                'endDate': entitlement.get('endDate'),
                                'entitlementType': entitlement.get('entitlementType', 'N/A'),
                                'itemNumber': entitlement.get('itemNumber', 'N/A')
                            })
                            if entitlement.get('endDate'):
                                try:
                                    end_date = datetime.fromisoformat(entitlement.get('endDate').replace('Z', '+00:00'))
                                    if latest_end_date is None or end_date > latest_end_date:
                                        latest_end_date = end_date
                                except:
                                    pass

                        if latest_end_date:
                            now = datetime.now(timezone.utc)
                            status = 'Em garantia' if latest_end_date > now else 'Expirado'
                            data_expiracao = latest_end_date.strftime('%d/%m/%Y')
                            results_map[st] = {
                                'serviceTag': st,
                                'serviceTagLimpo': st,
                                'modelo': modelo,
                                'dataExpiracao': data_expiracao,
                                'status': status,
                                'entitlements': valid_entitlements,
                                'dataSource': 'entitlements'
                            }
                        else:
                            results_map[st] = {
                                'serviceTag': st,
                                'serviceTagLimpo': st,
                                'modelo': modelo,
                                'dataExpiracao': 'Não disponível',
                                'status': 'Data de expiração desconhecida',
                                'entitlements': valid_entitlements,
                                'shipDate': warranty_data.get('shipDate'),
                                'orderNumber': warranty_data.get('orderNumber')
                            }
                elif response.status_code == 401:
                    # Tentar renovar token e repetir apenas essa batch
                    if self.get_access_token():
                        # força re-tentativa recursiva para a batch (simples: chamar novamente o bloco reduzido)
                        # para simplicidade, apenas retornar erro e confiar na rota chamadora para re-tentar
                        return {'error': 'Token expirado - reautenticação necessária', 'code': 'AUTH_ERROR'}
                    else:
                        return {'error': 'Erro de autenticação', 'code': 'AUTH_ERROR'}
                else:
                    return {'error': f'Erro interno da API Dell (HTTP {response.status_code})', 'code': 'DELL_API_ERROR'}

            except requests.exceptions.Timeout:
                return {'error': 'Timeout na conexão com Dell API', 'code': 'TIMEOUT_ERROR'}
            except Exception as e:
                print(f"❌ Erro inesperado ao consultar garantia Dell em batch: {e}")
                return {'error': 'Erro interno do servidor', 'code': 'INTERNAL_ERROR'}

        return results_map

class BackgroundSyncService:
    def __init__(self):
        self.sync_thread = None
        self.sync_running = False
        self.last_sync = None
        
    def start_background_sync(self):
        """Inicia sincronização em background"""
        if not self.sync_running:
            self.sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
            self.sync_thread.start()
            print("🔄 Serviço de sincronização iniciado")
    
    def _sync_loop(self):
        """Loop de sincronização em background"""
        self.sync_running = True
        while self.sync_running:
            try:
                self.sync_ad_to_sql()
                time.sleep(3600)  # Sync a cada hora
            except Exception as e:
                print(f"❌ Erro na sincronização background: {e}")
                time.sleep(300)  # Aguardar 5 minutos em caso de erro
    
    def sync_ad_to_sql(self):
        """Sincroniza dados do AD para SQL"""
        try:
            print("🔄 Iniciando sincronização AD → SQL")
            start_time = datetime.now()
            
            ad_computers = ad_manager.get_computers()
            
            if not ad_computers:
                print("❌ Nenhum computador encontrado no AD")
                return
            
            stats = {
                'found': len(ad_computers),
                'added': 0,
                'updated': 0,
                'errors': 0
            }
            
            for computer in ad_computers:
                try:
                    result = sql_manager.sync_computer_to_sql(computer)
                    if result:
                        stats['updated'] += 1
                    else:
                        stats['added'] += 1
                except Exception as e:
                    stats['errors'] += 1
                    print(f"❌ Erro ao sincronizar {computer.get('name', 'Unknown')}: {e}")
            
            sql_manager.log_sync_operation('incremental', 'completed', stats)
            
            self.last_sync = datetime.now()
            duration = (self.last_sync - start_time).total_seconds()
            
            print(f"✅ Sincronização concluída em {duration:.1f}s")
            print(f"📊 Encontrados: {stats['found']}, Atualizados: {stats['updated']}, Erros: {stats['errors']}")
            
        except Exception as e:
            print(f"❌ Erro na sincronização: {e}")
            sql_manager.log_sync_operation('incremental', 'failed', error_message=str(e))

# Instâncias globais
sql_manager = SQLManager()
ad_manager = ADManager()
ad_computer_manager = ADComputerManager()
dell_api = DellWarrantyAPI()
sync_service = BackgroundSyncService()

# =============================================================================
# MIDDLEWARE PARA CORS E DEBUGGING
# =============================================================================

@app.before_request
def log_request_info():
    """Log de informações da requisição para debugging"""
    print(f"🔍 REQUEST: {request.method} {request.path}")
    print(f"🔍 HEADERS: {dict(request.headers)}")
    print(f"🔍 ORIGIN: {request.headers.get('Origin', 'No Origin')}")
    print(f"🔍 CONTENT-TYPE: {request.headers.get('Content-Type', 'No Content-Type')}")
    print(f"🔍 CONTENT-LENGTH: {request.headers.get('Content-Length', 'No Content-Length')}")
    
    if request.method in ['POST', 'PUT', 'PATCH']:
        try:
            # Tentar pegar dados JSON
            if request.is_json:
                data = request.get_json()
                print(f"🔍 JSON DATA: {data}")
            else:
                print(f"🔍 NOT JSON - Content-Type: {request.content_type}")
                raw_data = request.get_data()
                print(f"🔍 RAW DATA: {raw_data}")
                print(f"🔍 RAW DATA (decoded): {raw_data.decode('utf-8', errors='ignore')}")
        except Exception as e:
            print(f"🔍 ERROR READING DATA: {e}")
            raw_data = request.get_data()
            print(f"🔍 RAW DATA FALLBACK: {raw_data}")

# Note: CORS preflight is handled by flask_cors extension configured at app creation.
# Manual preflight handling removed to avoid duplicate CORS headers.

@app.after_request
def after_request(response):
    """Add CORS headers to all responses"""
    # Let flask_cors extension manage Access-Control-* headers. Only add debug headers here.
    response.headers['X-Debug-Method'] = request.method
    response.headers['X-Debug-Path'] = request.path

    print(f"📤 RESPONSE: {response.status} - Headers: {dict(response.headers)}")
    return response

# Middleware adicional para debug específico da rota toggle-status
@app.before_request
def debug_toggle_status():
    """Debug específico para a rota toggle-status"""
    if '/toggle-status' in request.path:
        print(f"🎯 TOGGLE-STATUS MIDDLEWARE: {request.method} {request.path}")
        print(f"🎯 QUERY STRING: {request.query_string}")
        print(f"🎯 ARGS: {request.args}")
        print(f"🎯 FORM: {request.form}")
        print(f"🎯 FILES: {request.files}")
        
        if request.method == 'POST':
            print(f"🎯 IS_JSON: {request.is_json}")
            print(f"🎯 MIMETYPE: {request.mimetype}")
            print(f"🎯 CONTENT_TYPE: {request.content_type}")
            
            # Tentar múltiplas formas de ler os dados
            try:
                json_data = request.get_json(silent=True, force=False)
                print(f"🎯 JSON DATA (silent=True, force=False): {json_data}")
            except Exception as e:
                print(f"🎯 JSON ERROR 1: {e}")
            
            try:
                json_data = request.get_json(silent=False, force=True)
                print(f"🎯 JSON DATA (silent=False, force=True): {json_data}")
            except Exception as e:
                print(f"🎯 JSON ERROR 2: {e}")
            
            try:
                raw_data = request.get_data()
                print(f"🎯 RAW DATA: {raw_data}")
                print(f"🎯 RAW DATA DECODED: {raw_data.decode('utf-8', errors='ignore')}")
            except Exception as e:
                print(f"🎯 RAW DATA ERROR: {e}")

# =============================================================================
# ROTAS DA API
# =============================================================================

@app.route('/api/computers', methods=['GET'])
def get_computers():
    """Retorna computadores do SQL Server (ultra-rápido)"""
    try:
        use_sql = request.args.get('source', 'sql').lower() == 'sql'
        
        if use_sql:
            computers = sql_manager.get_computers_from_sql()
            return jsonify(computers)
        else:
            computers = ad_manager.get_computers()
            return jsonify(computers)
            
    except Exception as e:
        print(f"❌ Erro na rota /api/computers: {e}")
        try:
            print("🔄 Tentando fallback para AD...")
            computers = ad_manager.get_computers()
            return jsonify(computers)
        except Exception as ad_error:
            print(f"❌ Erro no fallback AD: {ad_error}")
            return jsonify({'error': 'Erro interno do servidor', 'details': str(e)}), 500

@app.route('/api/computers/sync', methods=['POST'])
def sync_computers():
    """Força sincronização manual AD → SQL"""
    try:
        sync_service.sync_ad_to_sql()
        return jsonify({
            'status': 'success',
            'message': 'Sincronização concluída',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/computers/<computer_name>/warranty', methods=['GET'])
def get_computer_warranty(computer_name):
    """Consulta garantia Dell para um computador específico"""
    try:
        warranty_info = dell_api.get_warranty_info(computer_name)
        
        if warranty_info and 'error' not in warranty_info:
            frontend_response = {
                'serviceTag': warranty_info.get('serviceTag', computer_name),
                'productLineDescription': warranty_info.get('modelo', 'N/A'),
                'systemDescription': warranty_info.get('modelo', 'N/A'),
                'warrantyEndDate': warranty_info.get('dataExpiracao', 'N/A'),
                'warrantyStatus': 'Active' if warranty_info.get('status') == 'Em garantia' else 'Expired',
                'entitlements': warranty_info.get('entitlements', []),
                'dataSource': warranty_info.get('dataSource', 'unknown')
            }
            return jsonify(frontend_response)
        else:
            return jsonify({'error': 'Warranty information not found'}), 404
            
    except Exception as e:
        print(f"❌ Erro ao consultar garantia para {computer_name}: {e}")
        return jsonify({'error': 'Warranty information not found'}), 500

@app.route('/api/warranty/service-tag/<service_tag>', methods=['GET'])
def get_warranty_by_service_tag(service_tag):
    """Consulta garantia Dell por service tag (rota específica; evita capturar caminhos como 'bulk-refresh')."""
    try:
        warranty_info = dell_api.get_warranty_info(service_tag)
        
        if 'error' in warranty_info:
            error_code = warranty_info.get('code', 'UNKNOWN_ERROR')
            
            if error_code in ['INVALID_SERVICE_TAG']:
                return jsonify({
                    'error': warranty_info['error'],
                    'code': error_code,
                    'serviceTag': service_tag
                }), 400
                
            elif error_code in ['SERVICE_TAG_NOT_FOUND', 'NO_WARRANTY_FOUND']:
                return jsonify({
                    'error': warranty_info['error'],
                    'code': error_code,
                    'serviceTag': service_tag
                }), 404
                
            elif error_code in ['AUTH_ERROR']:
                return jsonify({
                    'error': warranty_info['error'],
                    'code': error_code
                }), 401
                
            else:
                return jsonify({
                    'error': warranty_info['error'],
                    'code': error_code
                }), 500
        
        return jsonify(warranty_info), 200
        
    except Exception as e:
        print(f"❌ Erro na rota warranty: {e}")
        return jsonify({
            'error': 'Erro interno do servidor',
            'code': 'INTERNAL_ERROR'
        }), 500

# bulk-refresh endpoint (server-side batching using DellWarrantyChecker)
@app.route('/api/warranty/bulk-refresh', methods=['POST'])
def warranty_bulk_refresh():
    """Recebe um JSON com 'service_tags': [..] ou 'computers': [..] e faz consultas em lote
    para a API Dell usando a lógica thread-safe implementada em debug_c1wsb92.DellWarrantyChecker.

    Parâmetros opcionais no body:
    - batch_size (int, default 80)
    - max_workers (int, default 5)
    - request_delay (float, default 0.0)
    """
    try:
        data = request.get_json() or {}

        service_tags = data.get('service_tags') or []
        computers = data.get('computers') or []

        # Se vier lista de computadores, extrair service tags simples (remover prefixos conhecidos)
        if computers and (not service_tags):
            prefixes = ['SHQ', 'ESM', 'DIA', 'TOP', 'RUB', 'JAD', 'ONI', 'CLO']
            extracted = []
            for name in computers:
                if not name:
                    continue
                n = str(name).upper().strip()
                found = None
                for p in prefixes:
                    if n.startswith(p) and len(n) > len(p):
                        found = n[len(p):]
                        break
                if not found:
                    found = n if len(n) >= 5 else None
                if found:
                    extracted.append(found)
            service_tags = extracted

        if not service_tags or len(service_tags) == 0:
            return jsonify({'success': False, 'message': 'Nenhuma service_tag ou computers informados'}), 400

        # Params de performance
        batch_size = int(data.get('batch_size', 80))
        max_workers = int(data.get('max_workers', 5))
        request_delay = float(data.get('request_delay', 0.0))

        # Import local para evitar problemas de ordem/tempo de import
        from debug_c1wsb92 import DellWarrantyChecker

        # Deduplicar e normalizar
        uniq_tags = []
        seen = set()
        for t in service_tags:
            if not t:
                continue
            s = str(t).strip().upper()
            if s and s not in seen:
                seen.add(s)
                uniq_tags.append(s)

        checker = DellWarrantyChecker(
            servicetags_list=uniq_tags,
            client_id=DELL_CLIENT_ID,
            client_secret=DELL_CLIENT_SECRET,
            max_workers=max_workers,
            batch_size=batch_size,
            request_delay=request_delay
        )

        results = checker.run()
        duration = getattr(checker, 'last_run_duration_seconds', None)

        return jsonify({
            'success': True,
            'requested': len(uniq_tags),
            'returned': len(results),
            'duration_seconds': duration,
            'details': results
        }), 200

    except Exception as e:
        logger.error(f'❌ Erro no bulk-refresh: {e}')
        import traceback as _tb
        tb = _tb.format_exc()
        logger.error(tb)
        return jsonify({'success': False, 'error': str(e), 'trace': tb}), 500

# bulk-refresh removed - revert to single-machine refresh via existing endpoints

@app.route('/api/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """Retorna estatísticas do dashboard (do SQL)"""
    try:
        query = """
        SELECT 
            COUNT(*) as total_computers,
            SUM(CASE WHEN is_enabled = 1 THEN 1 ELSE 0 END) as enabled_computers,
            SUM(CASE WHEN is_enabled = 0 THEN 1 ELSE 0 END) as disabled_computers,
            SUM(CASE WHEN last_logon_timestamp > DATEADD(day, -30, GETDATE()) THEN 1 ELSE 0 END) as recent_logins,
            SUM(CASE WHEN last_logon_timestamp <= DATEADD(day, -30, GETDATE()) OR last_logon_timestamp IS NULL THEN 1 ELSE 0 END) as inactive_computers
        FROM computers 
        WHERE is_domain_controller = 0
        """
        
        stats_result = sql_manager.execute_query(query)
        stats = stats_result[0] if stats_result else {}
        
        org_query = """
        SELECT 
            o.name,
            o.code,
            COUNT(c.id) as count
        FROM organizations o
        LEFT JOIN computers c ON o.id = c.organization_id AND c.is_domain_controller = 0
        GROUP BY o.name, o.code
        ORDER BY count DESC
        """
        
        org_stats = sql_manager.execute_query(org_query)
        
        os_query = """
        SELECT 
            os.name,
            COUNT(c.id) as count
        FROM operating_systems os
        LEFT JOIN computers c ON os.id = c.operating_system_id AND c.is_domain_controller = 0
        GROUP BY os.name
        ORDER BY count DESC
        """
        
        os_stats = sql_manager.execute_query(os_query)
        
        return jsonify({
            'totalComputers': stats.get('total_computers', 0),
            'enabledComputers': stats.get('enabled_computers', 0),
            'disabledComputers': stats.get('disabled_computers', 0),
            'recentLogins': stats.get('recent_logins', 0),
            'inactiveComputers': stats.get('inactive_computers', 0),
            'organizationDistribution': [{'name': row['name'], 'code': row['code'], 'value': row['count']} for row in org_stats],
            'osDistribution': [{'name': row['name'], 'value': row['count']} for row in os_stats],
            'source': 'sql',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Erro nas estatísticas: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@app.route('/api/sync/status', methods=['GET'])
def get_sync_status():
    """Retorna status da sincronização"""
    try:
        query = """
        SELECT TOP 10
            sync_type,
            start_time,
            end_time,
            status,
            computers_found,
            computers_added,
            computers_updated,
            errors_count,
            error_message
        FROM sync_logs
        ORDER BY start_time DESC
        """
        
        logs = sql_manager.execute_query(query)
        
        return jsonify({
            'last_sync': sync_service.last_sync.isoformat() if sync_service.last_sync else None,
            'sync_running': sync_service.sync_running,
            'recent_logs': logs,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Erro no status de sync: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@app.route('/api/computers/search', methods=['GET'])
def search_computers():
    """Busca otimizada de computadores no SQL"""
    try:
        search_term = request.args.get('q', '').strip()
        organization = request.args.get('org', '')
        os_filter = request.args.get('os', '')
        status_filter = request.args.get('status', '')
        login_filter = request.args.get('login', '')
        limit = min(int(request.args.get('limit', 1000)), 5000)
        offset = int(request.args.get('offset', 0))
        
        where_conditions = ["c.is_domain_controller = 0"]
        params = []
        
        if search_term:
            where_conditions.append("(c.name LIKE ? OR c.description LIKE ? OR c.dns_hostname LIKE ?)")
            search_pattern = f"%{search_term}%"
            params.extend([search_pattern, search_pattern, search_pattern])
        
        if organization:
            where_conditions.append("o.code = ?")
            params.append(organization)
        
        if os_filter:
            where_conditions.append("os.name LIKE ?")
            params.append(f"%{os_filter}%")
        
        if status_filter == 'enabled':
            where_conditions.append("c.is_enabled = 1")
        elif status_filter == 'disabled':
            where_conditions.append("c.is_enabled = 0")
        
        if login_filter == 'recent':
            where_conditions.append("c.last_logon_timestamp > DATEADD(day, -7, GETDATE())")
        elif login_filter == 'old':
            where_conditions.append("c.last_logon_timestamp <= DATEADD(day, -30, GETDATE())")
        elif login_filter == 'never':
            where_conditions.append("c.last_logon_timestamp IS NULL")
        
        where_clause = " AND ".join(where_conditions)
        
        query = f"""
        SELECT 
            c.name, c.dns_hostname, c.distinguished_name as dn,
            c.is_enabled, c.description, c.last_logon_timestamp as lastLogon,
            c.created_date as created, c.user_account_control,
            o.name as organization_name, o.code as organization_code,
            os.name as os, os.version as osVersion
        FROM computers c
        LEFT JOIN organizations o ON c.organization_id = o.id
        LEFT JOIN operating_systems os ON c.operating_system_id = os.id
        WHERE {where_clause}
        ORDER BY c.name
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """
        
        params.extend([offset, limit])
        
        count_query = f"""
        SELECT COUNT(*) as total
        FROM computers c
        LEFT JOIN organizations o ON c.organization_id = o.id
        LEFT JOIN operating_systems os ON c.operating_system_id = os.id
        WHERE {where_clause}
        """
        
        count_params = params[:-2]
        
        results = sql_manager.execute_query(query, params)
        count_result = sql_manager.execute_query(count_query, count_params)
        
        total = count_result[0]['total'] if count_result else 0
        
        computers = []
        for row in results:
            computers.append({
                'name': row['name'],
                'dn': row['dn'],
                'lastLogon': row['lastLogon'].isoformat() if row['lastLogon'] else None,
                'os': row['os'] or 'N/A',
                'osVersion': row['osVersion'] or 'N/A',
                'created': row['created'].isoformat() if row['created'] else None,
                'description': row['description'] or '',
                'disabled': not row['is_enabled'],
                'userAccountControl': row['user_account_control'] or 0,
                'dnsHostName': row['dns_hostname'] or '',
                'organizationName': row['organization_name'] or '',
                'organizationCode': row['organization_code'] or ''
            })
        
        return jsonify({
            'computers': computers,
            'total': total,
            'limit': limit,
            'offset': offset,
            'has_more': (offset + limit) < total,
            'search_params': {
                'q': search_term,
                'org': organization,
                'os': os_filter,
                'status': status_filter,
                'login': login_filter
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Erro na busca: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

# =============================================================================
# ROTAS PARA TOGGLE DE STATUS DO COMPUTADOR
# =============================================================================

@app.route('/api/computers/<computer_name>/toggle-status', methods=['POST', 'OPTIONS'])
def toggle_computer_status(computer_name):
    """
    Ativa ou desativa computador no Active Directory
    Body: {"action": "enable" | "disable", "use_powershell": false}
    """
    print(f"🎯 TOGGLE-STATUS chamado: {request.method} para {computer_name}")
    
    # Handle preflight OPTIONS request explicitly
    if request.method == 'OPTIONS':
        print(f"🔄 OPTIONS request recebida para {computer_name}")
        response = jsonify({'status': 'OK', 'computer': computer_name})
        
        origin = request.headers.get('Origin')
        if origin:
            response.headers.add("Access-Control-Allow-Origin", origin)
        else:
            response.headers.add("Access-Control-Allow-Origin", "*")
            
        response.headers.add('Access-Control-Allow-Headers', "Content-Type,Authorization,Accept,X-Requested-With")
        response.headers.add('Access-Control-Allow-Methods', "POST,OPTIONS")
        response.headers.add('Access-Control-Max-Age', "3600")
        
        print(f"✅ OPTIONS response enviada com headers: {dict(response.headers)}")
        return response
    
    try:
        print(f"🔧 Processando POST request para {computer_name}")
        
        # Validar entrada
        if not computer_name or not computer_name.strip():
            print("❌ Nome da máquina vazio")
            return jsonify({
                'success': False,
                'message': 'Nome da máquina é obrigatório'
            }), 400
        
        # Verificar se há dados JSON
        try:
            data = request.get_json(force=True)
            print(f"📊 Dados recebidos: {data}")
        except Exception as json_error:
            print(f"❌ Erro ao processar JSON: {json_error}")
            print(f"📄 Raw data: {request.get_data()}")
            return jsonify({
                'success': False,
                'message': 'Dados JSON inválidos ou ausentes',
                'error': str(json_error)
            }), 400
        
        if not data or 'action' not in data:
            print("❌ Campo action ausente")
            return jsonify({
                'success': False,
                'message': 'Campo "action" é obrigatório no body',
                'received_data': data
            }), 400
        
        action = data['action'].lower()
        if action not in ['enable', 'disable']:
            print(f"❌ Ação inválida: {action}")
            return jsonify({
                'success': False,
                'message': 'Ação deve ser "enable" ou "disable"',
                'received_action': action
            }), 400
        
        computer_name = computer_name.strip()
        use_powershell = data.get('use_powershell', False)
        
        logger.info(f"🔄 Iniciando {action} para computador {computer_name}")
        print(f"🔄 Iniciando {action} para computador {computer_name}")
        
        try:
            # Primeira tentativa: LDAP direto (mais eficiente)
            if not use_powershell:
                logger.info(f"🔗 Tentando operação via LDAP...")
                print(f"🔗 Tentando operação via LDAP...")
                result = ad_computer_manager.toggle_computer_status(computer_name, action)
            else:
                raise Exception("PowerShell solicitado pelo usuário")
                
        except Exception as ldap_error:
            logger.warning(f"⚠️ LDAP falhou: {ldap_error}")
            print(f"⚠️ LDAP falhou: {ldap_error}")
            
            # Fallback: PowerShell
            logger.info(f"🔄 Tentando fallback via PowerShell...")
            print(f"🔄 Tentando fallback via PowerShell...")
            try:
                result = ad_computer_manager.toggle_computer_status_powershell(computer_name, action)
            except Exception as ps_error:
                logger.error(f"❌ PowerShell também falhou: {ps_error}")
                print(f"❌ PowerShell também falhou: {ps_error}")
                raise Exception(f"Ambos os métodos falharam. LDAP: {ldap_error}. PowerShell: {ps_error}")
        
        print(f"✅ Resultado da operação: {result}")
        
        # Atualizar cache SQL se a operação foi bem-sucedida
        if result.get('success') and not result.get('already_in_desired_state'):
            try:
                is_enabled = action == 'enable'
                new_uac = result.get('operation', {}).get('new_status', {}).get('userAccountControl')
                
                sql_updated = sql_manager.update_computer_status_in_sql(
                    computer_name, 
                    is_enabled, 
                    new_uac
                )
                
                if sql_updated:
                    logger.info(f"📊 Cache SQL atualizado para {computer_name}")
                    print(f"📊 Cache SQL atualizado para {computer_name}")
                else:
                    logger.warning(f"⚠️ Falha ao atualizar cache SQL para {computer_name}")
                    print(f"⚠️ Falha ao atualizar cache SQL para {computer_name}")
                    
            except Exception as sql_error:
                logger.warning(f"⚠️ Erro ao atualizar SQL (não crítico): {sql_error}")
                print(f"⚠️ Erro ao atualizar SQL (não crítico): {sql_error}")
        
        # Registrar log da operação
        try:
            operation_status = 'success' if result.get('success') else 'failed'
            details = json.dumps(result, default=str)
            
            sql_manager.log_computer_operation(
                computer_name=computer_name,
                operation=f'toggle_status_{action}',
                status=operation_status,
                details=details
            )
        except Exception as log_error:
            logger.warning(f"⚠️ Erro ao registrar log (não crítico): {log_error}")
            print(f"⚠️ Erro ao registrar log (não crítico): {log_error}")
        
        # Retornar resultado
        if result.get('success'):
            status_code = 200
            result['timestamp'] = datetime.now().isoformat()
            
            if not result.get('already_in_desired_state'):
                result['cache_updated'] = True
        else:
            status_code = 500
        
        print(f"📤 Retornando resposta: {status_code} - {result}")
        return jsonify(result), status_code
        
    except Exception as e:
        logger.error(f"❌ Erro na rota toggle-status: {e}")
        print(f"❌ Erro na rota toggle-status: {e}")
        
        # Registrar erro no log
        try:
            sql_manager.log_computer_operation(
                computer_name=computer_name,
                operation=f'toggle_status_{data.get("action", "unknown") if "data" in locals() else "unknown"}',
                status='error',
                error_message=str(e)
            )
        except:
            pass
        
        # Determinar código de erro apropriado
        error_message = str(e).lower()
        
        if 'não encontrada' in error_message or 'not found' in error_message:
            status_code = 404
            error_type = 'ComputerNotFound'
        elif 'autenticação' in error_message or 'authentication' in error_message:
            status_code = 401
            error_type = 'AuthenticationError'
        elif 'permissão' in error_message or 'permission' in error_message or 'access' in error_message:
            status_code = 403
            error_type = 'PermissionDenied'
        else:
            status_code = 500
            error_type = 'InternalError'
        
        error_response = {
            'success': False,
            'message': f'Erro ao {action if "action" in locals() else "processar"} máquina: {str(e)}',
            'error': {
                'type': error_type,
                'computer_name': computer_name,
                'action': data.get('action', 'unknown') if 'data' in locals() else 'unknown',
                'details': str(e),
                'timestamp': datetime.now().isoformat()
            }
        }
        
        print(f"📤 Retornando erro: {status_code} - {error_response}")
        return jsonify(error_response), status_code

@app.route('/api/computers/<computer_name>/status', methods=['GET'])
def get_computer_status(computer_name):
    """Retorna status atual de um computador no AD"""
    try:
        computer_info = ad_computer_manager.find_computer(computer_name)
        
        return jsonify({
            'success': True,
            'computer': {
                'name': computer_info['name'],
                'dn': computer_info['dn'],
                'enabled': not computer_info['disabled'],
                'disabled': computer_info['disabled'],
                'userAccountControl': computer_info['userAccountControl'],
                'description': computer_info['description'],
                'operatingSystem': computer_info['operatingSystem']
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar status de {computer_name}: {e}")
        
        if 'não encontrada' in str(e).lower() or 'not found' in str(e).lower():
            return jsonify({
                'success': False,
                'message': f'Computador {computer_name} não encontrado',
                'error': {'type': 'ComputerNotFound'}
            }), 404
        else:
            return jsonify({
                'success': False,
                'message': f'Erro ao consultar status: {str(e)}',
                'error': {'type': 'InternalError'}
            }), 500

@app.route('/api/test/toggle-computer', methods=['POST'])
def test_toggle_computer():
    """Endpoint de teste para toggle de computador (dry-run)"""
    try:
        data = request.get_json()
        computer_name = data.get('computer_name', '')
        action = data.get('action', 'enable')
        
        if not computer_name:
            return jsonify({
                'success': False,
                'message': 'computer_name é obrigatório'
            }), 400
        
        # Apenas buscar o computador sem modificar
        computer_info = ad_computer_manager.find_computer(computer_name)
        
        return jsonify({
            'success': True,
            'message': f'Teste realizado - computador encontrado',
            'computer': computer_info,
            'requested_action': action,
            'would_change': computer_info['disabled'] if action == 'enable' else not computer_info['disabled'],
            'note': 'Este é um teste - nenhuma modificação foi realizada',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro no teste: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

# =============================================================================
# ROTAS DE DEBUG E MONITORAMENTO
# =============================================================================

# =============================================================================
# ROTAS DE DEBUG E TESTE ESPECÍFICAS
# =============================================================================

@app.route('/api/test/simple-post', methods=['POST', 'OPTIONS'])
def test_simple_post():
    """Endpoint super simples para testar POST com CORS"""
    print(f"🧪 SIMPLE-POST: {request.method}")
    
    if request.method == 'OPTIONS':
        print("🔄 SIMPLE-POST OPTIONS")
        response = jsonify({'status': 'OPTIONS OK'})
        origin = request.headers.get('Origin')
        if origin:
            response.headers.add("Access-Control-Allow-Origin", origin)
        else:
            response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "Content-Type")
        response.headers.add('Access-Control-Allow-Methods', "POST,OPTIONS")
        return response
    
    try:
        print("📮 SIMPLE-POST Processing...")
        
        # Tentar diferentes formas de ler os dados
        data = None
        
        # Método 1: JSON padrão
        try:
            data = request.get_json()
            print(f"✅ JSON Method 1 success: {data}")
        except Exception as e:
            print(f"❌ JSON Method 1 failed: {e}")
        
        # Método 2: JSON forçado
        if data is None:
            try:
                data = request.get_json(force=True)
                print(f"✅ JSON Method 2 success: {data}")
            except Exception as e:
                print(f"❌ JSON Method 2 failed: {e}")
        
        # Método 3: Raw data
        if data is None:
            try:
                raw_data = request.get_data()
                print(f"📄 Raw data: {raw_data}")
                if raw_data:
                    import json
                    data = json.loads(raw_data.decode('utf-8'))
                    print(f"✅ JSON Method 3 success: {data}")
            except Exception as e:
                print(f"❌ JSON Method 3 failed: {e}")
        
        response_data = {
            'success': True,
            'message': 'Simple POST test successful',
            'received_data': data,
            'content_type': request.content_type,
            'is_json': request.is_json,
            'method': request.method,
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"✅ SIMPLE-POST Success: {response_data}")
        return jsonify(response_data), 200
        
    except Exception as e:
        print(f"❌ SIMPLE-POST Error: {e}")
        error_response = {
            'success': False,
            'error': str(e),
            'content_type': request.content_type,
            'is_json': request.is_json,
            'method': request.method,
            'timestamp': datetime.now().isoformat()
        }
        return jsonify(error_response), 500

@app.route('/api/test/cors', methods=['GET', 'POST', 'OPTIONS'])
def test_cors():
    """Endpoint de teste específico para CORS"""
    print(f"🧪 TEST-CORS: {request.method} - {dict(request.headers)}")
    
    if request.method == 'OPTIONS':
        print("🔄 CORS Test - OPTIONS recebida")
        response = jsonify({'method': 'OPTIONS', 'status': 'OK'})
        
        origin = request.headers.get('Origin')
        if origin:
            response.headers.add("Access-Control-Allow-Origin", origin)
        else:
            response.headers.add("Access-Control-Allow-Origin", "*")
            
        response.headers.add('Access-Control-Allow-Headers', "Content-Type,Authorization,Accept,X-Requested-With")
        response.headers.add('Access-Control-Allow-Methods', "GET,POST,OPTIONS")
        response.headers.add('Access-Control-Max-Age', "3600")
        
        print(f"✅ CORS Test - OPTIONS response: {dict(response.headers)}")
        return response
    
    elif request.method == 'POST':
        print("📮 CORS Test - POST recebida")
        try:
            data = request.get_json(force=True)
            print(f"📊 POST data: {data}")
            
            response_data = {
                'method': 'POST',
                'status': 'SUCCESS',
                'received_data': data,
                'headers_received': dict(request.headers),
                'timestamp': datetime.now().isoformat()
            }
            
            return jsonify(response_data), 200
            
        except Exception as e:
            print(f"❌ Erro no POST test: {e}")
            return jsonify({
                'method': 'POST',
                'status': 'ERROR',
                'error': str(e),
                'raw_data': request.get_data().decode('utf-8', errors='ignore')
            }), 400
    
    else:  # GET
        print("📤 CORS Test - GET recebida")
        return jsonify({
            'method': 'GET',
            'status': 'OK',
            'message': 'CORS test endpoint funcionando',
            'timestamp': datetime.now().isoformat()
        })

@app.route('/api/test/toggle-simple', methods=['POST', 'OPTIONS'])
def test_toggle_simple():
    """Endpoint de teste simplificado para toggle"""
    print(f"🧪 TEST-TOGGLE-SIMPLE: {request.method}")
    
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'OK'})
        origin = request.headers.get('Origin')
        if origin:
            response.headers.add("Access-Control-Allow-Origin", origin)
        else:
            response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "Content-Type")
        response.headers.add('Access-Control-Allow-Methods', "POST,OPTIONS")
        return response
    
    try:
        data = request.get_json(force=True)
        print(f"📊 Dados recebidos: {data}")
        
        # Simular processamento sem chamar AD
        return jsonify({
            'success': True,
            'message': 'Teste de toggle realizado com sucesso',
            'data_received': data,
            'simulated_action': data.get('action', 'unknown'),
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'raw_data': request.get_data().decode('utf-8', errors='ignore')
        }), 400

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check da API"""
    try:
        sql_test = sql_manager.execute_query("SELECT 1 as test")
        sql_ok = len(sql_test) > 0 and sql_test[0]['test'] == 1
        
        ad_ok = ad_manager.connect()
        if ad_manager.connection:
            ad_manager.connection.unbind()
        
        return jsonify({
            'status': 'OK',
            'timestamp': datetime.now().isoformat(),
            'port': 42057,
            'database': {
                'server': SQL_SERVER,
                'database': SQL_DATABASE,
                'status': 'connected' if sql_ok else 'disconnected'
            },
            'active_directory': {
                'server': AD_SERVER,
                'status': 'connected' if ad_ok else 'disconnected'
            },
            'sync_service': {
                'running': sync_service.sync_running,
                'last_sync': sync_service.last_sync.isoformat() if sync_service.last_sync else None
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'ERROR',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/debug/sql-test', methods=['GET'])
def debug_sql_test():
    """Testa conexão SQL e retorna dados básicos"""
    try:
        test_query = "SELECT COUNT(*) as total FROM computers WHERE is_domain_controller = 0"
        result = sql_manager.execute_query(test_query)
        
        sample_query = """
        SELECT TOP 5 
            name, dns_hostname, is_enabled, 
            os.name as os_name
        FROM computers c
        LEFT JOIN operating_systems os ON c.operating_system_id = os.id
        WHERE c.is_domain_controller = 0
        ORDER BY c.name
        """
        samples = sql_manager.execute_query(sample_query)
        
        return jsonify({
            'sql_connection': 'OK',
            'total_computers': result[0]['total'] if result else 0,
            'sample_computers': samples,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'sql_connection': 'ERROR',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/debug/ad-test', methods=['GET'])
def debug_ad_test():
    """Testa conexão AD e retorna dados básicos"""
    try:
        computers = ad_manager.get_computers()
        
        return jsonify({
            'ad_connection': 'OK',
            'total_computers': len(computers),
            'sample_computers': computers[:5] if computers else [],
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'ad_connection': 'ERROR',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/debug/full-test', methods=['GET'])
def debug_full_test():
    """Teste completo do sistema"""
    try:
        # Teste SQL
        sql_ok = False
        sql_count = 0
        sql_error = None
        
        try:
            test_result = sql_manager.execute_query("SELECT COUNT(*) as total FROM computers WHERE is_domain_controller = 0")
            sql_count = test_result[0]['total'] if test_result else 0
            sql_ok = True
        except Exception as e:
            sql_error = str(e)
        
        # Teste AD
        ad_ok = False
        ad_count = 0
        ad_error = None
        
        try:
            ad_computers = ad_manager.get_computers()
            ad_count = len(ad_computers)
            ad_ok = True
        except Exception as e:
            ad_error = str(e)
        
        # Teste get_computers_from_sql
        sql_computers = []
        sql_computers_error = None
        
        try:
            sql_computers = sql_manager.get_computers_from_sql()
        except Exception as e:
            sql_computers_error = str(e)
        
        return jsonify({
            'tests': {
                'sql_connection': {
                    'status': 'OK' if sql_ok else 'ERROR',
                    'computers_count': sql_count,
                    'error': sql_error
                },
                'ad_connection': {
                    'status': 'OK' if ad_ok else 'ERROR', 
                    'computers_count': ad_count,
                    'error': ad_error
                },
                'sql_computers_function': {
                    'status': 'OK' if not sql_computers_error else 'ERROR',
                    'computers_returned': len(sql_computers),
                    'error': sql_computers_error,
                    'sample': sql_computers[:2] if sql_computers else []
                }
            },
            'recommendations': {
                'use_sql': sql_ok and len(sql_computers) > 0,
                'use_ad_fallback': ad_ok,
                'sync_needed': sql_ok and ad_ok and sql_count == 0
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'test_error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/system/settings', methods=['GET'])
def get_system_settings():
    """Retorna configurações do sistema"""
    try:
        query = "SELECT setting_key, setting_value, setting_type, description FROM system_settings"
        settings = sql_manager.execute_query(query)
        
        return jsonify({
            'settings': {row['setting_key']: {
                'value': row['setting_value'],
                'type': row['setting_type'],
                'description': row['description']
            } for row in settings},
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Erro nas configurações: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

# =============================================================================
# TRATAMENTO DE ERROS GLOBAIS
# =============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handler para erros 404"""
    return jsonify({
        'error': 'Endpoint não encontrado',
        'message': 'A rota solicitada não existe',
        'timestamp': datetime.now().isoformat()
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handler para erros 500"""
    return jsonify({
        'error': 'Erro interno do servidor',
        'message': 'Ocorreu um erro inesperado no servidor',
        'timestamp': datetime.now().isoformat()
    }), 500

@app.errorhandler(Exception)
def handle_exception(e):
    """Handler para exceções não tratadas"""
    logger.error(f"❌ Exceção não tratada: {e}")
    import traceback as _traceback
    tb = _traceback.format_exc()
    logger.error(tb)

    # In debug we include full trace; otherwise still return trace for troubleshooting (remove in production)
    return jsonify({
        'error': 'Erro interno do servidor',
        'message': 'Ocorreu um erro inesperado',
        'details': str(e),
        'trace': tb,
        'timestamp': datetime.now().isoformat()
    }), 500

# =============================================================================
# ROTAS ADICIONAIS ÚTEIS
# =============================================================================

@app.route('/api/computers/<computer_name>/details', methods=['GET'])
def get_computer_details(computer_name):
    """Retorna detalhes completos de um computador específico"""
    try:
        # Buscar no SQL primeiro
        query = """
        SELECT 
            c.*,
            o.name as organization_name,
            o.code as organization_code,
            os.name as os_name,
            os.version as os_version,
            os.family as os_family
        FROM computers c
        LEFT JOIN organizations o ON c.organization_id = o.id
        LEFT JOIN operating_systems os ON c.operating_system_id = os.id
        WHERE c.name = ? AND c.is_domain_controller = 0
        """
        
        result = sql_manager.execute_query(query, [computer_name])
        
        if not result:
            return jsonify({
                'error': f'Computador {computer_name} não encontrado',
                'timestamp': datetime.now().isoformat()
            }), 404
        
        computer = result[0]
        
        # Formatar resposta
        details = {
            'name': computer['name'],
            'dn': computer['distinguished_name'],
            'enabled': computer['is_enabled'],
            'disabled': not computer['is_enabled'],
            'description': computer['description'] or '',
            'dnsHostName': computer['dns_hostname'] or '',
            'ipAddress': computer['ip_address'] or '',
            'macAddress': computer['mac_address'] or '',
            'userAccountControl': computer['user_account_control'] or 0,
            'primaryGroupID': computer['primary_group_id'] or 515,
            'lastLogon': computer['last_logon_timestamp'].isoformat() if computer['last_logon_timestamp'] else None,
            'created': computer['created_date'].isoformat() if computer['created_date'] else None,
            'lastSyncAd': computer['last_sync_ad'].isoformat() if computer['last_sync_ad'] else None,
            'organization': {
                'name': computer['organization_name'] or '',
                'code': computer['organization_code'] or ''
            },
            'operatingSystem': {
                'name': computer['os_name'] or 'N/A',
                'version': computer['os_version'] or 'N/A',
                'family': computer['os_family'] or 'N/A'
            },
            'source': 'sql',
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(details)
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar detalhes de {computer_name}: {e}")
        return jsonify({
            'error': 'Erro interno do servidor',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/organizations', methods=['GET'])
def get_organizations():
    """Retorna lista de organizações disponíveis"""
    try:
        query = """
        SELECT 
            o.id,
            o.name,
            o.code,
            o.description,
            COUNT(c.id) as computer_count
        FROM organizations o
        LEFT JOIN computers c ON o.id = c.organization_id AND c.is_domain_controller = 0
        GROUP BY o.id, o.name, o.code, o.description
        ORDER BY o.name
        """
        
        organizations = sql_manager.execute_query(query)
        
        return jsonify({
            'organizations': organizations,
            'total': len(organizations),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar organizações: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@app.route('/api/operating-systems', methods=['GET'])
def get_operating_systems():
    """Retorna lista de sistemas operacionais disponíveis"""
    try:
        query = """
        SELECT 
            os.id,
            os.name,
            os.version,
            os.family,
            COUNT(c.id) as computer_count
        FROM operating_systems os
        LEFT JOIN computers c ON os.id = c.operating_system_id AND c.is_domain_controller = 0
        GROUP BY os.id, os.name, os.version, os.family
        ORDER BY computer_count DESC, os.name
        """
        
        operating_systems = sql_manager.execute_query(query)
        
        return jsonify({
            'operating_systems': operating_systems,
            'total': len(operating_systems),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar sistemas operacionais: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@app.route('/api/computers/bulk-action', methods=['POST'])
def bulk_computer_action():
    """Executa ação em lote em múltiplos computadores"""
    try:
        data = request.get_json()
        
        if not data or 'computers' not in data or 'action' not in data:
            return jsonify({
                'success': False,
                'message': 'Campos "computers" e "action" são obrigatórios'
            }), 400
        
        computers = data['computers']
        action = data['action'].lower()
        
        if action not in ['enable', 'disable']:
            return jsonify({
                'success': False,
                'message': 'Ação deve ser "enable" ou "disable"'
            }), 400
        
        if not isinstance(computers, list) or len(computers) == 0:
            return jsonify({
                'success': False,
                'message': 'Lista de computadores não pode estar vazia'
            }), 400
        
        # Limitar número de computadores por segurança
        if len(computers) > 50:
            return jsonify({
                'success': False,
                'message': 'Máximo de 50 computadores por operação em lote'
            }), 400
        
        results = []
        success_count = 0
        error_count = 0
        
        for computer_name in computers:
            try:
                computer_name = computer_name.strip()
                if not computer_name:
                    continue
                
                # Executar ação no computador
                result = ad_computer_manager.toggle_computer_status(computer_name, action)
                
                if result.get('success'):
                    success_count += 1
                    
                    # Atualizar cache SQL
                    try:
                        is_enabled = action == 'enable'
                        new_uac = result.get('operation', {}).get('new_status', {}).get('userAccountControl')
                        sql_manager.update_computer_status_in_sql(computer_name, is_enabled, new_uac)
                    except Exception as sql_error:
                        logger.warning(f"⚠️ Erro ao atualizar SQL para {computer_name}: {sql_error}")
                else:
                    error_count += 1
                
                results.append({
                    'computer': computer_name,
                    'success': result.get('success', False),
                    'message': result.get('message', 'Erro desconhecido'),
                    'already_in_desired_state': result.get('already_in_desired_state', False)
                })
                
            except Exception as e:
                error_count += 1
                results.append({
                    'computer': computer_name,
                    'success': False,
                    'message': str(e),
                    'error': True
                })
        
        # Registrar operação em lote
        try:
            sql_manager.log_computer_operation(
                computer_name=f'BULK_OPERATION_{len(computers)}_computers',
                operation=f'bulk_{action}',
                status='completed',
                details=json.dumps({
                    'total': len(computers),
                    'success': success_count,
                    'errors': error_count,
                    'action': action
                }, default=str)
            )
        except Exception as log_error:
            logger.warning(f"⚠️ Erro ao registrar log de operação em lote: {log_error}")
        
        return jsonify({
            'success': True,
            'message': f'Operação em lote concluída: {success_count} sucessos, {error_count} erros',
            'summary': {
                'total': len(computers),
                'success_count': success_count,
                'error_count': error_count,
                'action': action
            },
            'results': results,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Erro na operação em lote: {e}")
        return jsonify({
            'success': False,
            'message': f'Erro na operação em lote: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500
# =============================================================================
# CLASSE DHCP MANAGER CORRIGIDA PARA COMPATIBILIDADE COM FRONTEND
# =============================================================================

from pypsrp.client import Client
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

class DHCPManager:
    """Gerenciador para busca de MACs por service tag nos servidores DHCP"""
    
    def __init__(self):
        # Mapeamento CORRETO de organizações para servidores DHCP
        self.org_to_servers = {
            "SHQ": ["ESMDC02"],     # SHQ usa servidor da Esmeralda
            "ESMERALDA": ["ESMDC02"], # Esmeralda
            "DIAMANTE": ["DIADC02"],  # Diamante
            "TOPAZIO": ["TOPDC02"],   # Topázio
            "RUBI": ["RUBDC02"],      # Rubi
            "JADE": ["JADDC02"],      # Jade
            "ONIX": ["ONIDC02"],      # Ônix
        }
        
        # Mapeamento de prefixos para organizações (como o frontend identifica)
        self.prefix_to_org = {
            "DIA": "DIAMANTE",
            "ESM": "ESMERALDA", 
            "JAD": "JADE",
            "RUB": "RUBI",
            "ONI": "ONIX",
            "TOP": "TOPAZIO",
            "SHQ": "SHQ",
            "CLO": "SHQ"  # Centro Logístico usa mesmo servidor da sede
        }
        
        # Todos os servidores DHCP disponíveis
        self.all_servers = [
            "DIADC02",  # DIAMANTE
            "ESMDC02",  # ESMERALDA
            "JADDC02",  # JADE
            "RUBDC02",  # RUBI
            "ONIDC02",  # ONIX
            "TOPDC02",  # TOPAZIO
        ]
        
        # Prefixos possíveis para busca
        self.prefixos = ["SHQ", "ESM", "DIA", "TOP", "RUB", "JAD", "ONI", "CLO"]
        
        # Credenciais - mesmas do AD
        self.usuario = AD_USERNAME
        self.senha = AD_PASSWORD
    
    def get_organization_from_prefix(self, prefix):
        """Converte prefixo para nome da organização"""
        return self.prefix_to_org.get(prefix.upper(), prefix.upper())
    
    def testar_conexao_servidor(self, servidor):
        """Testa conexão com um servidor DHCP específico"""
        try:
            client = Client(
                server=servidor,
                username=self.usuario,
                password=self.senha,
                ssl=False,
                cert_validation=False,
                connection_timeout=10,
                operation_timeout=10
            )
            
            # Teste simples
            script = "Write-Output 'OK'"
            output, streams, had_errors = client.execute_ps(script)
            
            if had_errors or 'OK' not in output:
                return None
                
            return client
            
        except Exception as e:
            logger.warning(f"Falha ao conectar em {servidor}: {str(e)[:100]}")
            return None
    
    def buscar_service_tag_servidor(self, servidor, service_tag):
        """Busca service tag em um servidor específico"""
        resultado = {
            'servidor': servidor,
            'status': 'erro',
            'macs': [],
            'erro': None,
            'tempo': 0
        }
        
        inicio = time.time()
        
        try:
            # Conectar ao servidor
            client = self.testar_conexao_servidor(servidor)
            if not client:
                resultado['status'] = 'conexao_falhou'
                resultado['erro'] = 'Não foi possível conectar'
                return resultado
            
            logger.info(f"✅ Conectado DHCP: {servidor}")
            
            # Preparar padrões de busca
            patterns = [service_tag]  # Service tag pura
            
            # Adicionar prefixos
            for prefixo in self.prefixos:
                patterns.extend([
                    f"{prefixo}-{service_tag}",      # SHQ-H2Z1ZP3
                    f"{prefixo}_{service_tag}",      # SHQ_H2Z1ZP3
                    f"{prefixo} {service_tag}",      # SHQ H2Z1ZP3
                    f"{prefixo}{service_tag}",       # SHQH2Z1ZP3
                ])
            
            # Script PowerShell otimizado
            patterns_str = "', '".join(patterns)
            script = f"""
            $patterns = @('{patterns_str}')
            $filters = Get-DhcpServerv4Filter -List Allow
            $found = @()
            
            foreach ($pattern in $patterns) {{
                $matches = $filters | Where-Object {{$_.Description -like "*$pattern*"}}
                if ($matches) {{
                    $found += $matches
                }}
            }}
            
            # Remover duplicatas
            $unique = $found | Sort-Object MacAddress -Unique
            
            if ($unique) {{
                foreach ($filter in $unique) {{
                    Write-Output "MAC:$($filter.MacAddress)"
                    Write-Output "DESC:$($filter.Description)"
                    Write-Output "---"
                }}
            }} else {{
                Write-Output "NENHUM_ENCONTRADO"
            }}
            """
            
            # Executar busca
            output, streams, had_errors = client.execute_ps(script)
            
            if had_errors:
                resultado['status'] = 'erro_dhcp'
                resultado['erro'] = '; '.join([str(error) for error in streams.error])
                return resultado
            
            # Processar resultados
            if 'NENHUM_ENCONTRADO' in output:
                resultado['status'] = 'nao_encontrado'
            else:
                # Parsear resultados
                lines = output.strip().split('\n')
                macs = []
                current_mac = None
                
                for line in lines:
                    line = line.strip()
                    if line.startswith('MAC:'):
                        current_mac = line.replace('MAC:', '').strip()
                    elif line.startswith('DESC:') and current_mac:
                        desc = line.replace('DESC:', '').strip()
                        
                        # Identificar padrão encontrado
                        pattern_encontrado = "sem_prefixo"
                        for pattern in patterns:
                            if pattern.upper() in desc.upper():
                                pattern_encontrado = pattern
                                break
                        
                        macs.append({
                            'mac': current_mac,
                            'description': desc,
                            'pattern_found': pattern_encontrado,
                            'server': servidor,
                            'filter_type': 'Allow',  # Só estamos buscando Allow por enquanto
                            'mac_address': current_mac,  # Alias para compatibilidade
                            'match_field': 'description',  # Campo onde foi encontrado
                            'name': ''  # Vazio por enquanto
                        })
                        
                        logger.info(f"✅ {servidor}: MAC {current_mac} - Padrão: {pattern_encontrado}")
                
                resultado['macs'] = macs
                resultado['status'] = 'encontrado' if macs else 'nao_encontrado'
        
        except Exception as e:
            resultado['status'] = 'erro'
            resultado['erro'] = str(e)
            logger.error(f"❌ Erro DHCP {servidor}: {str(e)[:100]}")
        
        finally:
            resultado['tempo'] = time.time() - inicio
        
        return resultado

# Instanciar o DHCP Manager
dhcp_manager = DHCPManager()

# =============================================================================
# ROTA API DHCP FILTERS - COMPATÍVEL COM FRONTEND
# =============================================================================

@app.route('/api/dhcp/filters/<organization>', methods=['GET'])
def get_dhcp_filters_by_organization(organization):
    """
    Busca filtros DHCP por organização e service tag
    
    URL: /api/dhcp/filters/SHQ?service_tag=SHQH2Z1ZP3&include_filters=false
    
    Formato de resposta compatível com o frontend
    """
    try:
        # Validar organização (aceita tanto prefixos quanto nomes completos)
        organization_upper = organization.upper().strip()
        
        # Converter prefixo para nome da organização se necessário
        if organization_upper in dhcp_manager.prefix_to_org:
            ship_name = dhcp_manager.prefix_to_org[organization_upper]
        else:
            ship_name = organization_upper
        
        # Obter parâmetros da query
        service_tag = request.args.get('service_tag', '').strip()
        include_filters = request.args.get('include_filters', 'false').lower() == 'true'
        
        if not service_tag:
            return jsonify({
                'success': False,
                'message': 'Parâmetro service_tag é obrigatório',
                'organization': organization
            }), 400
        
        # Remover prefixo da service tag se existir
        original_service_tag = service_tag.upper()
        clean_service_tag = service_tag.upper()
        
        # Remove prefixos conhecidos da service tag
        for prefix in dhcp_manager.prefixos:
            if clean_service_tag.startswith(prefix):
                clean_service_tag = clean_service_tag[len(prefix):]
                break
        
        logger.info(f"🔍 API DHCP Filters: Org={organization}, Ship={ship_name}, ServiceTag={original_service_tag}, Clean={clean_service_tag}")
        
        # Determinar servidores alvo baseado na organização
        servidores_alvo = dhcp_manager.org_to_servers.get(ship_name, dhcp_manager.all_servers)
        
        # Executar busca nos servidores da organização
        macs_encontrados = []
        servidores_consultados = 0
        servidores_com_erro = 0
        tempo_total = 0
        
        for servidor in servidores_alvo:
            try:
                resultado = dhcp_manager.buscar_service_tag_servidor(servidor, clean_service_tag)
                tempo_total += resultado['tempo']
                
                if resultado['status'] == 'encontrado':
                    servidores_consultados += 1
                    # Adicionar MACs encontrados
                    for mac_info in resultado['macs']:
                        macs_encontrados.append(mac_info)
                
                elif resultado['status'] == 'nao_encontrado':
                    servidores_consultados += 1
                else:
                    servidores_com_erro += 1
                    logger.warning(f"⚠️ Erro no servidor {servidor}: {resultado.get('erro', 'Erro desconhecido')}")
                    
            except Exception as e:
                servidores_com_erro += 1
                logger.error(f"❌ Erro ao consultar {servidor}: {e}")
        
        # Remover duplicatas baseado no MAC
        macs_unicos = {}
        for mac_info in macs_encontrados:
            mac = mac_info['mac']
            if mac not in macs_unicos:
                macs_unicos[mac] = mac_info
        
        macs_finais = list(macs_unicos.values())
        
        # Preparar resposta NO FORMATO QUE O FRONTEND ESPERA
        if macs_finais:
            # RESPOSTA DE SUCESSO - formato compatível com frontend
            response_data = {
                'ship_name': ship_name,
                'dhcp_server': servidores_alvo[0] if servidores_alvo else 'N/A',
                'service_tag': original_service_tag,
                'service_tag_found': True,
                'search_results': macs_finais,  # Frontend espera este campo
                'filters': {
                    'total': len(macs_finais),
                    'allow_count': len([m for m in macs_finais if m.get('filter_type') == 'Allow']),
                    'deny_count': len([m for m in macs_finais if m.get('filter_type') == 'Deny'])
                },
                'timestamp': datetime.now().isoformat(),
                'source': 'dhcp_filters'
            }
            
            logger.info(f"✅ API DHCP: {len(macs_finais)} MAC(s) encontrado(s) para {organization}/{original_service_tag}")
            status_code = 200
        else:
            # RESPOSTA DE NÃO ENCONTRADO - formato compatível com frontend
            response_data = {
                'ship_name': ship_name,
                'dhcp_server': servidores_alvo[0] if servidores_alvo else 'N/A',
                'service_tag': original_service_tag,
                'service_tag_found': False,
                'search_results': [],
                'error': f'Máquina não encontrada nos filtros DHCP',
                'filters': {
                    'total': 0,
                    'allow_count': 0,
                    'deny_count': 0
                },
                'timestamp': datetime.now().isoformat(),
                'source': 'dhcp_filters_not_found'
            }
            
            logger.info(f"❌ API DHCP: Nenhum MAC encontrado para {organization}/{original_service_tag}")
            status_code = 200  # Frontend espera 200 mesmo quando não encontra
        
        return jsonify(response_data), status_code
        
    except Exception as e:
        logger.error(f"❌ Erro na rota DHCP filters para {organization}: {e}")
        
        # RESPOSTA DE ERRO - formato compatível com frontend
        error_response = {
            'ship_name': organization.upper(),
            'error': f'Erro ao consultar filtros DHCP: {str(e)}',
            'debug_info': {
                'organization': organization,
                'service_tag': request.args.get('service_tag', ''),
                'error_details': str(e)
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(error_response), 200  # Frontend espera 200 mesmo em erro

@app.route('/api/dhcp/search', methods=['POST'])
def dhcp_search_post():
    """
    Busca DHCP via POST - compatível com frontend
    Body: {"service_tag": "SHQH2Z1ZP3", "ships": ["SHQ"]}
    """
    try:
        data = request.get_json()
        
        if not data or 'service_tag' not in data:
            return jsonify({
                'success': False,
                'message': 'Campo "service_tag" é obrigatório no body'
            }), 400
        
        service_tag = data['service_tag'].strip()
        ships = data.get('ships', [])
        
        logger.info(f"🔍 API DHCP Search POST: ServiceTag={service_tag}, Ships={ships}")
        
        # Determinar servidores alvo
        if ships and len(ships) > 0:
            servidores_alvo = []
            for ship in ships:
                ship_name = dhcp_manager.get_organization_from_prefix(ship)
                ship_servers = dhcp_manager.org_to_servers.get(ship_name, [])
                servidores_alvo.extend(ship_servers)
            # Remover duplicatas
            servidores_alvo = list(set(servidores_alvo))
        else:
            # Buscar em todos os servidores
            servidores_alvo = dhcp_manager.all_servers
        
        # Remover prefixo da service tag se existir
        clean_service_tag = service_tag.upper()
        for prefix in dhcp_manager.prefixos:
            if clean_service_tag.startswith(prefix):
                clean_service_tag = clean_service_tag[len(prefix):]
                break
        
        # Executar busca
        resultados_por_servidor = []
        macs_encontrados = []
        
        for servidor in servidores_alvo:
            try:
                resultado = dhcp_manager.buscar_service_tag_servidor(servidor, clean_service_tag)
                
                if resultado['status'] == 'encontrado':
                    for mac_info in resultado['macs']:
                        macs_encontrados.append(mac_info)
                    
                    # Adicionar resultado por servidor
                    resultados_por_servidor.append({
                        'ship_name': 'UNKNOWN',  # TODO: mapear servidor para navio
                        'dhcp_server': servidor,
                        'matches': resultado['macs'],
                        'filters_summary': {
                            'total': len(resultado['macs']),
                            'allow_count': len([m for m in resultado['macs'] if m.get('filter_type') == 'Allow']),
                            'deny_count': 0
                        }
                    })
                    
            except Exception as e:
                logger.error(f"❌ Erro ao consultar {servidor}: {e}")
        
        # Remover duplicatas
        macs_unicos = {}
        for mac_info in macs_encontrados:
            mac = mac_info['mac']
            if mac not in macs_unicos:
                macs_unicos[mac] = mac_info
        
        macs_finais = list(macs_unicos.values())
        
        # Resposta no formato que o frontend espera
        response_data = {
            'found': len(macs_finais) > 0,
            'service_tag': service_tag,
            'clean_service_tag': clean_service_tag,
            'results': resultados_por_servidor,
            'total_matches': len(macs_finais),
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"❌ Erro na rota DHCP search POST: {e}")
        return jsonify({
            'found': False,
            'error': str(e),
            'service_tag': request.json.get('service_tag', '') if request.json else '',
            'timestamp': datetime.now().isoformat()
        }), 200

@app.route('/api/dhcp/test-connection', methods=['GET'])
def test_dhcp_connections():
    """Testa conectividade com todos os servidores DHCP"""
    try:
        resultados = {}
        
        for servidor in dhcp_manager.all_servers:
            inicio = time.time()
            try:
                client = dhcp_manager.testar_conexao_servidor(servidor)
                tempo = time.time() - inicio
                
                if client:
                    resultados[servidor] = {
                        'status': 'conectado',
                        'tempo': round(tempo, 2),
                        'erro': None
                    }
                else:
                    resultados[servidor] = {
                        'status': 'falhou',
                        'tempo': round(tempo, 2),
                        'erro': 'Falha na conexão'
                    }
            except Exception as e:
                tempo = time.time() - inicio
                resultados[servidor] = {
                    'status': 'erro',
                    'tempo': round(tempo, 2),
                    'erro': str(e)
                }
        
        # Calcular estatísticas
        total_servidores = len(resultados)
        servidores_ok = sum(1 for r in resultados.values() if r['status'] == 'conectado')
        servidores_erro = total_servidores - servidores_ok
        
        return jsonify({
            'success': True,
            'resumo': {
                'total_servidores': total_servidores,
                'servidores_ok': servidores_ok,
                'servidores_erro': servidores_erro,
                'percentual_sucesso': round((servidores_ok / total_servidores) * 100, 1)
            },
            'detalhes': resultados,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Erro no teste de conexão DHCP: {e}")
        return jsonify({
            'success': False,
            'message': 'Erro ao testar conexões DHCP',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/dhcp/servers', methods=['GET'])
def get_dhcp_servers():
    """Retorna lista de servidores DHCP configurados"""
    return jsonify({
        'success': True,
        'servers': dhcp_manager.all_servers,
        'organization_mapping': dhcp_manager.org_to_servers,
        'prefix_mapping': dhcp_manager.prefix_to_org,
        'supported_prefixes': dhcp_manager.prefixos,
        'total_servers': len(dhcp_manager.all_servers),
        'dhcp_user': dhcp_manager.usuario,
        'timestamp': datetime.now().isoformat()
    })
# =============================================================================
# SERVIÇO PARA ÚLTIMO USUÁRIO VIA EVENT LOG DO ACTIVE DIRECTORY
# =============================================================================

from pypsrp.client import Client
import re
import time
from datetime import datetime, timedelta
import json
import logging

class ADEventLogLastUserService:
    """
    Serviço para descobrir último usuário via Event Log do Active Directory
    Conecta apenas no Domain Controller e busca eventos centralizadamente
    """
    
    def __init__(self):
        # Usar as mesmas credenciais do AD
        self.usuario = AD_USERNAME
        self.senha = AD_PASSWORD
        
        # Determinar Domain Controller automaticamente
        self.domain_controller = self._get_domain_controller()
        
        # Event IDs relevantes para logons (eventos que chegam no DC)
        self.logon_event_ids = {
            4624: "Successful Logon",
            4768: "Kerberos Authentication Ticket (TGT) was requested",
            4769: "Kerberos Service Ticket was requested", 
            4770: "Kerberos Service Ticket was renewed",
            4771: "Kerberos pre-authentication failed",
            4776: "Computer attempted to validate credentials (NTLM)",
            4778: "Session was reconnected to Window Station",
            4779: "Session was disconnected from Window Station"
        }
        
        # Tipos de logon
        self.logon_types = {
            2: "Interactive (Console)",
            3: "Network", 
            4: "Batch",
            5: "Service",
            7: "Unlock",
            8: "NetworkCleartext",
            9: "NewCredentials",
            10: "RemoteInteractive (RDP)",
            11: "CachedInteractive"
        }
        
        # Configurações
        self.connection_timeout = 15
        self.operation_timeout = 60
        self.max_events = 200
    
    def _get_domain_controller(self):
        """Determina o Domain Controller baseado na configuração do AD"""
        # Extrair servidor do AD_SERVER
        if AD_SERVER:
            # Remove ldap:// se existir
            dc_name = AD_SERVER.replace('ldap://', '').replace('ldaps://', '')
            return dc_name
        
        # Fallback para extrair do DN
        if AD_BASE_DN:
            # Converter DC=snm,DC=local para snm.local
            domain_parts = []
            for part in AD_BASE_DN.split(','):
                if part.strip().upper().startswith('DC='):
                    domain_parts.append(part.strip()[3:])
            
            if domain_parts:
                domain = '.'.join(domain_parts)
                return f"DC.{domain}"  # Convenção comum
        
        # Fallback final
        return "CLODC02.snm.local"  # Baseado no seu ambiente
    
    def conectar_domain_controller(self):
        """Conecta ao Domain Controller para acessar Event Logs"""
        try:
            logger.info(f"🔗 Conectando ao Domain Controller: {self.domain_controller}")
            
            client = Client(
                server=self.domain_controller,
                username=self.usuario,
                password=self.senha,
                ssl=False,
                cert_validation=False,
                connection_timeout=self.connection_timeout,
                operation_timeout=self.operation_timeout
            )
            
            # Teste de conectividade
            test_script = """
            try {
                $dc = Get-ADDomainController -Current
                Write-Output "DC_INFO: $($dc.Name) - $($dc.Domain) - $($dc.OperatingSystem)"
                Write-Output "CONNECTION_OK"
            } catch {
                Write-Output "DC_TEST_ERROR: $($_.Exception.Message)"
            }
            """
            
            output, streams, had_errors = client.execute_ps(test_script)
            
            if not had_errors and 'CONNECTION_OK' in output:
                logger.info(f"✅ Conectado ao DC: {self.domain_controller}")
                logger.info(f"📊 Info do DC: {output.split('DC_INFO:')[1].split('CONNECTION_OK')[0].strip() if 'DC_INFO:' in output else 'N/A'}")
                return client
            else:
                logger.error(f"❌ Teste de conectividade falhou no DC: {output}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erro ao conectar no DC {self.domain_controller}: {e}")
            return None
    
    def buscar_ultimo_logon_por_computador(self, computer_name, dias_historico=30):
        """
        Busca último logon de um computador específico via Event Log do AD
        """
        resultado = {
            'computer_name': computer_name,
            'success': False,
            'last_user': None,
            'last_logon_time': None,
            'logon_type': None,
            'recent_logons': [],
            'error': None,
            'connection_method': 'ad_eventlog',
            'search_method': 'domain_controller_events',
            'search_time': 0,
            'computer_found': None,
            'total_time': 0,
            'events_found': 0
        }
        
        inicio = time.time()
        
        try:
            # Conectar ao Domain Controller
            client = self.conectar_domain_controller()
            if not client:
                resultado['error'] = f'Não foi possível conectar ao Domain Controller {self.domain_controller}'
                resultado['connection_method'] = 'dc_connection_failed'
                return resultado
            
            logger.info(f"🔍 Buscando eventos de logon para {computer_name} no DC")
            
            # Preparar nomes de busca (com e sem domínio)
            computer_names_to_search = [
                computer_name.upper(),
                computer_name.lower(),
                f"{computer_name.upper()}$",  # Computer account
                f"{computer_name.lower()}$"
            ]
            
            # Script PowerShell para buscar eventos no DC
            data_inicio = (datetime.now() - timedelta(days=dias_historico)).strftime('%Y-%m-%d')
            computer_names_str = "', '".join(computer_names_to_search)
            
            script = f"""
            try {{
                $startDate = Get-Date "{data_inicio}"
                $computerNames = @('{computer_names_str}')
                $maxEvents = {self.max_events}
                $results = @()
                
                Write-Output "INFO: Buscando eventos desde $startDate para computador {computer_name}"
                Write-Output "INFO: Nomes de busca: $($computerNames -join ', ')"
                
                # Buscar eventos 4624 (Successful Logon) no DC
                try {{
                    $events = Get-WinEvent -FilterHashtable @{{
                        LogName='Security'
                        ID=@(4624, 4768, 4769)  # Logon + Kerberos tickets
                        StartTime=$startDate
                    }} -MaxEvents $maxEvents -ErrorAction Stop | 
                    Sort-Object TimeCreated -Descending
                    
                    Write-Output "INFO: Encontrados $($events.Count) eventos de autenticação no DC"
                    
                    foreach ($event in $events) {{
                        try {{
                            $xml = [xml]$event.ToXml()
                            $eventData = $xml.Event.EventData.Data
                            
                            # Campos específicos para cada tipo de evento
                            $targetUserName = ($eventData | Where-Object {{$_.Name -eq 'TargetUserName'}}).InnerText
                            $targetDomainName = ($eventData | Where-Object {{$_.Name -eq 'TargetDomainName'}}).InnerText
                            $workstationName = ($eventData | Where-Object {{$_.Name -eq 'WorkstationName'}}).InnerText
                            $sourceNetworkAddress = ($eventData | Where-Object {{$_.Name -eq 'IpAddress'}}).InnerText
                            $logonType = ($eventData | Where-Object {{$_.Name -eq 'LogonType'}}).InnerText
                            $logonProcessName = ($eventData | Where-Object {{$_.Name -eq 'LogonProcessName'}}).InnerText
                            
                            # Para eventos Kerberos (4768, 4769)
                            if ($event.Id -in @(4768, 4769)) {{
                                $targetUserName = ($eventData | Where-Object {{$_.Name -eq 'TargetUserName'}}).InnerText
                                $targetDomainName = ($eventData | Where-Object {{$_.Name -eq 'TargetDomainName'}}).InnerText
                                $clientAddress = ($eventData | Where-Object {{$_.Name -eq 'ClientAddress'}}).InnerText
                                $workstationName = ($eventData | Where-Object {{$_.Name -eq 'WorkstationName'}}).InnerText
                                
                                # Para Kerberos, usar o campo ClientAddress como source
                                if ($clientAddress) {{ $sourceNetworkAddress = $clientAddress }}
                            }}
                            
                            # Verificar se o evento está relacionado ao computador alvo
                            $isTargetComputer = $false
                            
                            # Verificar por nome da workstation
                            if ($workstationName) {{
                                foreach ($searchName in $computerNames) {{
                                    if ($workstationName -like "*$($searchName.Replace('$', ''))*") {{
                                        $isTargetComputer = $true
                                        break
                                    }}
                                }}
                            }}
                            
                            # Verificar se é uma conta de computador
                            if ($targetUserName -and $targetUserName.EndsWith('$')) {{
                                foreach ($searchName in $computerNames) {{
                                    if ($targetUserName -eq $searchName) {{
                                        $isTargetComputer = $true
                                        break
                                    }}
                                }}
                            }}
                            
                            # Se encontrou evento relacionado ao computador
                            if ($isTargetComputer -and $targetUserName -and 
                                $targetUserName -ne 'SYSTEM' -and 
                                $targetUserName -ne 'ANONYMOUS LOGON' -and
                                $targetUserName -notlike 'DWM-*' -and
                                $targetDomainName -ne 'NT AUTHORITY') {{
                                
                                $eventInfo = @{{
                                    'TimeCreated' = $event.TimeCreated.ToString('yyyy-MM-ddTHH:mm:ss.fffZ')
                                    'UserName' = $targetUserName
                                    'Domain' = $targetDomainName
                                    'FullUser' = if ($targetDomainName -and $targetUserName -notlike '*$') {{ 
                                        "$targetDomainName\\$targetUserName" 
                                    }} else {{ 
                                        $targetUserName 
                                    }}
                                    'LogonType' = $logonType
                                    'LogonTypeDesc' = switch ($logonType) {{
                                        '2' {{ 'Interactive (Console)' }}
                                        '3' {{ 'Network' }}
                                        '7' {{ 'Unlock' }}
                                        '10' {{ 'RemoteInteractive (RDP)' }}
                                        '11' {{ 'CachedInteractive' }}
                                        default {{ "Type $logonType" }}
                                    }}
                                    'WorkstationName' = $workstationName
                                    'SourceIP' = if ($sourceNetworkAddress -and $sourceNetworkAddress -ne '-' -and $sourceNetworkAddress -ne '::1') {{ 
                                        $sourceNetworkAddress 
                                    }} else {{ 
                                        'N/A' 
                                    }}
                                    'LogonProcess' = $logonProcessName
                                    'EventId' = $event.Id
                                    'EventType' = switch ($event.Id) {{
                                        4624 {{ 'Logon' }}
                                        4768 {{ 'Kerberos TGT' }}
                                        4769 {{ 'Kerberos Service' }}
                                        default {{ 'Auth' }}
                                    }}
                                    'ComputerMatched' = $workstationName
                                }}
                                
                                # Filtrar contas de computador para a lista final se não são o target
                                if (-not $targetUserName.EndsWith('$') -or $targetUserName -in $computerNames) {{
                                    $results += $eventInfo
                                }}
                            }}
                        }} catch {{
                            Write-Output "WARN: Erro ao processar evento $($event.Id): $($_.Exception.Message)"
                        }}
                    }}
                    
                    if ($results.Count -eq 0) {{
                        Write-Output "NO_EVENTS_FOR_COMPUTER"
                    }} else {{
                        Write-Output "SUCCESS: $($results.Count) eventos encontrados para {computer_name}"
                        $results | ConvertTo-Json -Depth 3 -Compress
                    }}
                    
                }} catch [System.Exception] {{
                    if ($_.Exception.Message -like "*No events were found*") {{
                        Write-Output "NO_EVENTS_IN_PERIOD"
                    }} else {{
                        Write-Output "ERROR_EVENTLOG: $($_.Exception.Message)"
                    }}
                }}
                
            }} catch {{
                Write-Output "ERROR_GENERAL: $($_.Exception.Message)"
            }}
            """
            
            # Executar script
            logger.info(f"🔍 Executando busca de eventos no DC para {computer_name}")
            output, streams, had_errors = client.execute_ps(script)
            
            # Log de debug
            if streams.error:
                logger.warning(f"⚠️ PowerShell stderr: {'; '.join([str(error) for error in streams.error])}")
            
            # Processar resultado
            output_lines = output.strip().split('\n') if output else []
            
            if any('NO_EVENTS_IN_PERIOD' in line for line in output_lines):
                resultado['error'] = f'Nenhum evento de autenticação encontrado nos últimos {dias_historico} dias no DC'
                resultado['search_method'] = 'dc_events_no_events_in_period'
                return resultado
            
            if any('NO_EVENTS_FOR_COMPUTER' in line for line in output_lines):
                resultado['error'] = f'Nenhum evento de logon encontrado para {computer_name} nos logs do DC'
                resultado['search_method'] = 'dc_events_no_events_for_computer'
                resultado['computer_found'] = False
                return resultado
            
            if any('ERROR_EVENTLOG:' in line for line in output_lines):
                error_line = next((line for line in output_lines if 'ERROR_EVENTLOG:' in line), '')
                resultado['error'] = error_line.replace('ERROR_EVENTLOG: ', '')
                return resultado
            
            if any('ERROR_GENERAL:' in line for line in output_lines):
                error_line = next((line for line in output_lines if 'ERROR_GENERAL:' in line), '')
                resultado['error'] = error_line.replace('ERROR_GENERAL: ', '')
                return resultado
            
            # Buscar linha com JSON dos resultados
            json_content = None
            for line in output_lines:
                if line.strip().startswith('[') or line.strip().startswith('{'):
                    json_content = line.strip()
                    break
            
            if not json_content:
                # Tentar juntar todas as linhas que podem ser JSON
                potential_json = '\n'.join([line for line in output_lines 
                                          if not line.startswith('INFO:') 
                                          and not line.startswith('WARN:') 
                                          and not line.startswith('SUCCESS:')
                                          and line.strip()])
                if potential_json:
                    json_content = potential_json
            
            if not json_content:
                resultado['error'] = 'Resposta do DC não contém dados de eventos válidos'
                logger.error(f"Saída DC: {output[:500]}")
                return resultado
            
            # Parse do JSON retornado
            try:
                events_data = json.loads(json_content)
                
                # Se é um único evento, converter para lista
                if isinstance(events_data, dict):
                    events_data = [events_data]
                
                if events_data and len(events_data) > 0:
                    # Filtrar eventos de contas de usuário (não computador)
                    user_events = [event for event in events_data 
                                 if not event.get('UserName', '').endswith('$')]
                    
                    if user_events:
                        # Ordenar por data (mais recente primeiro)
                        user_events.sort(key=lambda x: x['TimeCreated'], reverse=True)
                        
                        # Último logon de usuário
                        last_event = user_events[0]
                        
                        resultado['success'] = True
                        resultado['last_user'] = last_event.get('FullUser', last_event.get('UserName', 'Usuário desconhecido'))
                        resultado['last_logon_time'] = last_event.get('TimeCreated')
                        resultado['logon_type'] = last_event.get('LogonTypeDesc', f"Type {last_event.get('LogonType', 'Unknown')}")
                        resultado['computer_found'] = True
                        resultado['events_found'] = len(events_data)
                        
                        # Detalhes de logons recentes (até 5 de usuários)
                        resultado['recent_logons'] = []
                        for event in user_events[:5]:
                            resultado['recent_logons'].append({
                                'user': event.get('FullUser', event.get('UserName', 'Usuário desconhecido')),
                                'time': event.get('TimeCreated'),
                                'logon_type': event.get('LogonTypeDesc', f"Type {event.get('LogonType', 'Unknown')}"),
                                'workstation': event.get('WorkstationName', ''),
                                'source_ip': event.get('SourceIP', 'N/A'),
                                'logon_process': event.get('LogonProcess', ''),
                                'event_id': event.get('EventId', 0),
                                'event_type': event.get('EventType', 'Auth')
                            })
                        
                        logger.info(f"✅ Último logon via DC para {computer_name}: {resultado['last_user']} em {resultado['last_logon_time']}")
                    else:
                        resultado['error'] = 'Apenas eventos de conta de computador encontrados (nenhum usuário)'
                        resultado['computer_found'] = True
                        resultado['events_found'] = len(events_data)
                else:
                    resultado['error'] = 'Nenhum evento válido encontrado após processamento'
                    
            except json.JSONDecodeError as json_error:
                resultado['error'] = f'Erro ao processar dados de eventos do DC: {str(json_error)}'
                logger.error(f"Erro JSON: {json_content[:500]}")
                
        except Exception as e:
            resultado['error'] = f'Erro geral na busca de eventos no DC: {str(e)}'
            logger.error(f"❌ Erro ao buscar eventos no DC para {computer_name}: {e}")
        
        finally:
            resultado['search_time'] = round(time.time() - inicio, 2)
            resultado['total_time'] = resultado['search_time']
        
        return resultado
    
    def buscar_logon_por_service_tag_via_ad(self, service_tag, dias_historico=30):
        """
        Busca último logon usando service tag para encontrar a máquina no AD,
        depois busca eventos no DC
        """
        resultado = {
            'service_tag': service_tag,
            'success': False,
            'computer_found': False,
            'computer_name': None,
            'last_user': None,
            'last_logon_time': None,
            'logon_type': None,
            'recent_logons': [],
            'error': None,
            'search_method': None,
            'total_time': 0,
            'events_found': 0
        }
        
        inicio_total = time.time()
        
        try:
            # 1. Encontrar máquina no AD pela service tag
            computer_name = self.encontrar_maquina_por_service_tag(service_tag)
            
            if not computer_name:
                resultado['error'] = f'Máquina com service tag {service_tag} não encontrada no Active Directory'
                resultado['search_method'] = 'ad_search_failed'
                return resultado
            
            resultado['computer_found'] = True
            resultado['computer_name'] = computer_name
            resultado['search_method'] = 'ad_search_then_dc_events'
            
            # 2. Buscar eventos no DC para a máquina encontrada
            logon_result = self.buscar_ultimo_logon_por_computador(computer_name, dias_historico)
            
            # Copiar resultados
            if logon_result['success']:
                resultado['success'] = True
                resultado['last_user'] = logon_result['last_user']
                resultado['last_logon_time'] = logon_result['last_logon_time']
                resultado['logon_type'] = logon_result['logon_type']
                resultado['recent_logons'] = logon_result['recent_logons']
                resultado['events_found'] = logon_result['events_found']
            else:
                resultado['error'] = logon_result.get('error', 'Erro desconhecido ao buscar eventos no DC')
                
        except Exception as e:
            resultado['error'] = str(e)
            logger.error(f"❌ Erro geral ao buscar logon por service tag {service_tag}: {e}")
        
        finally:
            resultado['total_time'] = round(time.time() - inicio_total, 2)
        
        return resultado
    
    def encontrar_maquina_por_service_tag(self, service_tag):
        """Encontra nome da máquina no AD usando service tag"""
        try:
            # Limpar service tag (remover prefixos se houver)
            clean_service_tag = service_tag.upper().strip()
            original_service_tag = clean_service_tag
            
            # Lista de possíveis prefixos para remover
            prefixes = ['SHQ', 'ESM', 'DIA', 'TOP', 'RUB', 'JAD', 'ONI', 'CLO']
            for prefix in prefixes:
                if clean_service_tag.startswith(prefix):
                    clean_service_tag = clean_service_tag[len(prefix):]
                    break
            
            logger.info(f"🔍 Buscando máquina por service tag: {original_service_tag} (limpa: {clean_service_tag})")
            
            # Conectar ao AD
            if not ad_manager.connect():
                logger.error("❌ Falha ao conectar no AD")
                return None
            
            try:
                # Buscar computadores que contenham a service tag no nome ou descrição
                search_patterns = [clean_service_tag, original_service_tag]
                
                for pattern in search_patterns:
                    search_filter = f'''(&
                        (objectClass=computer)
                        (|(cn=*{pattern}*)(description=*{pattern}*))
                    )'''
                    
                    search_filter = ''.join(search_filter.split())
                    
                    ad_manager.connection.search(
                        search_base=AD_BASE_DN,
                        search_filter=search_filter,
                        search_scope=SUBTREE,
                        attributes=['cn', 'description', 'dNSHostName']
                    )
                    
                    # Procurar correspondência exata
                    for entry in ad_manager.connection.entries:
                        computer_name = str(entry.cn)
                        description = str(entry.description) if entry.description else ''
                        
                        # Verificar se service tag está no nome ou descrição
                        if (pattern.upper() in computer_name.upper() or 
                            pattern.upper() in description.upper()):
                            
                            logger.info(f"✅ Máquina encontrada: {computer_name} para service tag {original_service_tag}")
                            return computer_name
                
                logger.info(f"❌ Nenhuma máquina encontrada para service tag {original_service_tag}")
                return None
                
            finally:
                ad_manager.connection.unbind()
                
        except Exception as e:
            logger.error(f"❌ Erro ao buscar máquina por service tag {service_tag}: {e}")
            return None
    
    def testar_conectividade_dc(self):
        """Testa conectividade com o Domain Controller"""
        try:
            client = self.conectar_domain_controller()
            
            if client:
                # Teste adicional - verificar logs de segurança
                test_script = """
                try {
                    $dc = Get-ADDomainController -Current
                    $logInfo = Get-WinEvent -ListLog Security
                    $recentEvents = Get-WinEvent -LogName Security -MaxEvents 5 | Measure-Object
                    
                    $info = @{
                        'DCName' = $dc.Name
                        'Domain' = $dc.Domain
                        'OS' = $dc.OperatingSystem
                        'SecurityLogEnabled' = $logInfo.IsEnabled
                        'SecurityLogSize' = $logInfo.FileSize
                        'RecentEventsCount' = $recentEvents.Count
                        'PowerShellVersion' = $PSVersionTable.PSVersion.ToString()
                    }
                    $info | ConvertTo-Json -Compress
                } catch {
                    Write-Output "DC_INFO_ERROR: $($_.Exception.Message)"
                }
                """
                
                output, streams, had_errors = client.execute_ps(test_script)
                
                return {
                    'success': True,
                    'domain_controller': self.domain_controller,
                    'dc_info': output if not had_errors else None,
                    'errors': [str(error) for error in streams.error] if streams.error else []
                }
            else:
                return {
                    'success': False,
                    'domain_controller': self.domain_controller,
                    'error': 'Não foi possível conectar ao Domain Controller'
                }
                
        except Exception as e:
            return {
                'success': False,
                'domain_controller': self.domain_controller,
                'error': str(e)
            }

# Instanciar o serviço de AD Event Log
ad_eventlog_service = ADEventLogLastUserService()

# =============================================================================
# ROTAS API PARA ÚLTIMO USUÁRIO VIA AD EVENT LOG
# =============================================================================

@app.route('/api/computers/<computer_name>/last-user', methods=['GET'])
def get_last_user_by_computer_ad_eventlog(computer_name):
    """
    Obtém último usuário via Event Log do Active Directory - SEM CONEXÃO REMOTA
    
    Query params:
    - days: número de dias para buscar no histórico (padrão: 30)
    """
    try:
        dias_historico = int(request.args.get('days', 30))
        
        logger.info(f"🔍 Buscando último usuário via AD Event Log para: {computer_name}")
        
        resultado = ad_eventlog_service.buscar_ultimo_logon_por_computador(computer_name, dias_historico)
        
        # Sempre retornar 200 com informações detalhadas
        response_data = {
            'success': resultado['success'],
            'computer_name': computer_name,
            'computer_found': resultado.get('computer_found'),
            'last_user': resultado['last_user'],
            'last_logon_time': resultado['last_logon_time'],
            'logon_type': resultado['logon_type'],
            'connection_method': resultado['connection_method'],
            'search_method': resultado['search_method'],
            'search_time': resultado['search_time'],
            'total_time': resultado['total_time'],
            'recent_logons': resultado['recent_logons'],
            'events_found': resultado.get('events_found', 0),
            'timestamp': datetime.now().isoformat()
        }
        
        # Adicionar error apenas se houver
        if resultado['error']:
            response_data['error'] = resultado['error']
        
        logger.info(f"📊 Resultado AD EventLog para {computer_name}: Success={resultado['success']}, User={resultado['last_user']}, Events={resultado.get('events_found', 0)}")
        
        return jsonify(response_data), 200
            
    except Exception as e:
        logger.error(f"❌ Erro na rota AD EventLog last-user para {computer_name}: {e}")
        return jsonify({
            'success': False,
            'computer_name': computer_name,
            'computer_found': False,
            'error': f'Erro interno: {str(e)}',
            'search_method': 'api_error',
            'connection_method': 'ad_eventlog',
            'timestamp': datetime.now().isoformat()
        }), 200

@app.route('/api/service-tag/<service_tag>/last-user', methods=['GET'])
def get_last_user_by_service_tag_ad_eventlog(service_tag):
    """
    Obtém último usuário usando service tag via AD Event Log
    
    Query params:
    - days: número de dias para buscar no histórico (padrão: 30)
    """
    try:
        dias_historico = int(request.args.get('days', 30))
        
        logger.info(f"🔍 Buscando último usuário via AD Event Log para service tag: {service_tag}")
        
        resultado = ad_eventlog_service.buscar_logon_por_service_tag_via_ad(service_tag, dias_historico)
        
        # Sempre retornar 200 com informações detalhadas
        response_data = {
            'success': resultado['success'],
            'service_tag': service_tag,
            'computer_name': resultado['computer_name'],
            'last_user': resultado['last_user'],
            'last_logon_time': resultado['last_logon_time'],
            'logon_type': resultado['logon_type'],
            'search_method': resultado['search_method'],
            'total_time': resultado['total_time'],
            'recent_logons': resultado['recent_logons'],
            'events_found': resultado.get('events_found', 0),
            'timestamp': datetime.now().isoformat()
        }
        
        # Adicionar error apenas se houver
        if resultado['error']:
            response_data['error'] = resultado['error']
        
        logger.info(f"📊 Resultado AD EventLog service tag {service_tag}: Success={resultado['success']}, Computer={resultado['computer_name']}, User={resultado['last_user']}")
        
        return jsonify(response_data), 200
            
    except Exception as e:
        logger.error(f"❌ Erro na rota AD EventLog service tag {service_tag}: {e}")
        return jsonify({
            'success': False,
            'service_tag': service_tag,
            'computer_found': False,
            'error': f'Erro interno: {str(e)}',
            'search_method': 'api_error',
            'timestamp': datetime.now().isoformat()
        }), 200

@app.route('/api/last-user/test-dc-connection', methods=['GET'])
def test_ad_eventlog_dc_connection():
    """Testa conectividade com o Domain Controller"""
    try:
        logger.info(f"🧪 Testando conectividade com DC: {ad_eventlog_service.domain_controller}")
        
        result = ad_eventlog_service.testar_conectividade_dc()
        
        if result['success']:
            return jsonify({
                'success': True,
                'domain_controller': result['domain_controller'],
                'status': 'connected',
                'message': f'Conexão estabelecida com sucesso ao DC {result["domain_controller"]}',
                'dc_info': result.get('dc_info'),
                'timestamp': datetime.now().isoformat()
            }), 200
        else:
            return jsonify({
                'success': False,
                'domain_controller': result['domain_controller'],
                'status': 'connection_failed',
                'message': result.get('error', 'Não foi possível conectar ao Domain Controller'),
                'timestamp': datetime.now().isoformat()
            }), 200
            
    except Exception as e:
        logger.error(f"❌ Erro no teste de conectividade DC: {e}")
        return jsonify({
            'success': False,
            'domain_controller': ad_eventlog_service.domain_controller,
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 200

@app.route('/api/last-user/search-events-sample', methods=['GET'])
def search_events_sample():
    """
    Endpoint para testar busca de eventos no DC sem filtrar por computador específico
    Útil para debug e verificar se eventos estão sendo gerados
    """
    try:
        dias_historico = int(request.args.get('days', 1))  # Padrão 1 dia
        max_events = int(request.args.get('max_events', 50))
        
        logger.info(f"🧪 Testando busca de eventos no DC (últimos {dias_historico} dias)")
        
        client = ad_eventlog_service.conectar_domain_controller()
        if not client:
            return jsonify({
                'success': False,
                'error': f'Não foi possível conectar ao DC {ad_eventlog_service.domain_controller}',
                'timestamp': datetime.now().isoformat()
            }), 200
        
        data_inicio = (datetime.now() - timedelta(days=dias_historico)).strftime('%Y-%m-%d')
        
        script = f"""
        try {{
            $startDate = Get-Date "{data_inicio}"
            $maxEvents = {max_events}
            
            Write-Output "INFO: Buscando eventos desde $startDate (máximo $maxEvents eventos)"
            
            $events = Get-WinEvent -FilterHashtable @{{
                LogName='Security'
                ID=@(4624, 4768, 4769)
                StartTime=$startDate
            }} -MaxEvents $maxEvents -ErrorAction Stop | 
            Sort-Object TimeCreated -Descending
            
            $sample = @()
            foreach ($event in $events[0..9]) {{  # Primeiros 10 eventos
                $xml = [xml]$event.ToXml()
                $eventData = $xml.Event.EventData.Data
                
                $targetUserName = ($eventData | Where-Object {{$_.Name -eq 'TargetUserName'}}).InnerText
                $workstationName = ($eventData | Where-Object {{$_.Name -eq 'WorkstationName'}}).InnerText
                $logonType = ($eventData | Where-Object {{$_.Name -eq 'LogonType'}}).InnerText
                
                $sample += @{{
                    'TimeCreated' = $event.TimeCreated.ToString('yyyy-MM-ddTHH:mm:ss')
                    'EventId' = $event.Id
                    'UserName' = $targetUserName
                    'WorkstationName' = $workstationName
                    'LogonType' = $logonType
                }}
            }}
            
            $result = @{{
                'TotalEvents' = $events.Count
                'SampleEvents' = $sample
                'SearchPeriod' = "$startDate até agora"
            }}
            
            $result | ConvertTo-Json -Depth 3 -Compress
            
        }} catch {{
            Write-Output "ERROR: $($_.Exception.Message)"
        }}
        """
        
        output, streams, had_errors = client.execute_ps(script)
        
        if had_errors or 'ERROR:' in output:
            error_msg = '; '.join([str(error) for error in streams.error]) if streams.error else output
            return jsonify({
                'success': False,
                'error': f'Erro na busca de eventos: {error_msg}',
                'timestamp': datetime.now().isoformat()
            }), 200
        
        try:
            result_data = json.loads(output.strip())
            return jsonify({
                'success': True,
                'domain_controller': ad_eventlog_service.domain_controller,
                'search_period_days': dias_historico,
                'total_events_found': result_data.get('TotalEvents', 0),
                'sample_events': result_data.get('SampleEvents', []),
                'search_period': result_data.get('SearchPeriod', ''),
                'timestamp': datetime.now().isoformat()
            }), 200
            
        except json.JSONDecodeError:
            return jsonify({
                'success': False,
                'error': 'Resposta do DC não é JSON válido',
                'raw_output': output[:500],
                'timestamp': datetime.now().isoformat()
            }), 200
            
    except Exception as e:
        logger.error(f"❌ Erro no teste de eventos sample: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/last-user/debug-ad-eventlog/<computer_name>', methods=['GET'])
def debug_ad_eventlog_service(computer_name):
    """Endpoint de debug específico para o serviço AD EventLog"""
    try:
        debug_info = {
            'computer_name': computer_name,
            'domain_controller': ad_eventlog_service.domain_controller,
            'timestamp': datetime.now().isoformat(),
            'tests': {}
        }
        
        # Teste 1: Conectividade com DC
        logger.info(f"🔍 Debug - Teste de conectividade DC para {computer_name}")
        dc_result = ad_eventlog_service.testar_conectividade_dc()
        debug_info['tests']['dc_connectivity'] = dc_result
        
        # Teste 2: Busca no AD para encontrar a máquina
        logger.info(f"🔍 Debug - Verificando se máquina existe no AD")
        try:
            if ad_manager.connect():
                search_filter = f"(&(objectClass=computer)(cn={computer_name}))"
                ad_manager.connection.search(
                    search_base=AD_BASE_DN,
                    search_filter=search_filter,
                    search_scope=SUBTREE,
                    attributes=['cn', 'description', 'dNSHostName', 'lastLogonTimestamp']
                )
                
                if ad_manager.connection.entries:
                    entry = ad_manager.connection.entries[0]
                    debug_info['tests']['ad_lookup'] = {
                        'found': True,
                        'computer_name': str(entry.cn),
                        'description': str(entry.description) if entry.description else '',
                        'dns_hostname': str(entry.dNSHostName) if entry.dNSHostName else '',
                        'last_logon_ad': str(entry.lastLogonTimestamp) if entry.lastLogonTimestamp else None
                    }
                else:
                    debug_info['tests']['ad_lookup'] = {
                        'found': False,
                        'error': 'Computer not found in Active Directory'
                    }
                
                ad_manager.connection.unbind()
            else:
                debug_info['tests']['ad_lookup'] = {
                    'error': 'Failed to connect to Active Directory'
                }
        except Exception as ad_error:
            debug_info['tests']['ad_lookup'] = {
                'error': f'AD lookup error: {str(ad_error)}'
            }
        
        # Teste 3: Busca de eventos no DC (se DC conectou)
        if dc_result['success']:
            logger.info(f"🔍 Debug - Teste de busca de eventos no DC para {computer_name}")
            events_result = ad_eventlog_service.buscar_ultimo_logon_por_computador(computer_name, 7)
            debug_info['tests']['dc_event_search'] = {
                'success': events_result['success'],
                'last_user': events_result['last_user'],
                'error': events_result['error'],
                'search_time': events_result['search_time'],
                'events_found': events_result.get('events_found', 0),
                'recent_logons_count': len(events_result['recent_logons'])
            }
        else:
            debug_info['tests']['dc_event_search'] = {
                'skipped': True,
                'reason': 'DC connectivity test failed'
            }
        
        # Teste 4: Verificar se é service tag
        if computer_name.upper() != computer_name.lower():  # Tem letras
            logger.info(f"🔍 Debug - Testando como service tag")
            service_tag_result = ad_eventlog_service.encontrar_maquina_por_service_tag(computer_name)
            debug_info['tests']['service_tag_lookup'] = {
                'attempted': True,
                'computer_found': service_tag_result is not None,
                'computer_name': service_tag_result
            }
        else:
            debug_info['tests']['service_tag_lookup'] = {
                'attempted': False,
                'reason': 'Computer name appears to be hostname, not service tag'
            }
        
        # Resumo e recomendações
        debug_info['summary'] = {
            'can_connect_dc': dc_result['success'],
            'exists_in_ad': debug_info['tests']['ad_lookup'].get('found', False),
            'can_get_events': debug_info['tests']['dc_event_search'].get('success', False) if 'dc_event_search' in debug_info['tests'] else False,
            'method': 'ad_eventlog_centralized',
            'recommendations': []
        }
        
        # Recomendações específicas para AD EventLog
        if not dc_result['success']:
            debug_info['summary']['recommendations'].append('Verificar conectividade WinRM com Domain Controller')
            debug_info['summary']['recommendations'].append('Confirmar credenciais de acesso ao DC')
        
        if not debug_info['tests']['ad_lookup'].get('found', False):
            debug_info['summary']['recommendations'].append('Verificar se nome da máquina está correto no AD')
        
        if dc_result['success'] and not debug_info['tests']['dc_event_search'].get('success', False):
            debug_info['summary']['recommendations'].append('Verificar se eventos de logon estão sendo gerados no DC')
            debug_info['summary']['recommendations'].append('Confirmar se auditoria de logon está habilitada no domínio')
            debug_info['summary']['recommendations'].append('Verificar se máquina está gerando eventos de autenticação')
        
        return jsonify(debug_info), 200
        
    except Exception as e:
        logger.error(f"❌ Erro no debug AD EventLog para {computer_name}: {e}")
        return jsonify({
            'success': False,
            'computer_name': computer_name,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# =============================================================================
# FUNÇÃO PARA EXTRAIR SERVICE TAG (compatibilidade com frontend)
# =============================================================================

def extract_service_tag_from_computer_name(computer_name):
    """
    Função auxiliar para extrair service tag do nome da máquina
    Replica a lógica do frontend para compatibilidade
    """
    # Tentar extrair service tag do nome da máquina
    name = computer_name.upper()
    
    # Prefixos conhecidos
    prefixes = ['SHQ', 'ESM', 'DIA', 'TOP', 'RUB', 'JAD', 'ONI', 'CLO']
    
    for prefix in prefixes:
        if name.startswith(prefix):
            possible_service_tag = name[len(prefix):]
            # Se sobrou algo que parece service tag (letras e números)
            if possible_service_tag and len(possible_service_tag) >= 5:
                return possible_service_tag
    
    return computer_name  # Retorna o nome original se não conseguir extrair

# =============================================================================
# SUBSTITUIÇÃO AUTOMÁTICA DO SERVIÇO ORIGINAL
# =============================================================================

# Substituir a instância global do serviço original
if 'last_user_service' in globals():
    print("🔄 Substituindo last_user_service pelo ad_eventlog_service...")
    
# Criar alias para compatibilidade
last_user_service = ad_eventlog_service

print(f"✅ AD EventLog Service inicializado com DC: {ad_eventlog_service.domain_controller}")

# =============================================================================
# ROTAS DE GARANTIA DELL - ADICIONAR À API FLASK EXISTENTE
# =============================================================================

@app.route('/api/computers/warranty-summary', methods=['GET'])
def get_warranty_summary():
    """
    Retorna resumo das garantias Dell para todas as máquinas
    Rota específica para o frontend com filtros de garantia
    """
    try:
        logger.info('📊 Buscando resumo de garantias Dell...')
        
        # Query otimizada para buscar apenas dados essenciais de garantia
        query = """
        SELECT 
            dw.computer_id,
            dw.warranty_status,
            dw.warranty_start_date,
            dw.warranty_end_date,
            dw.last_updated,
            dw.last_error,
            dw.service_tag,
            dw.service_tag_clean,
            dw.product_line_description,
            dw.system_description,
            c.name as computer_name,
            c.is_enabled,
            c.last_logon_timestamp
        FROM dell_warranty dw
        INNER JOIN computers c ON dw.computer_id = c.id
        WHERE c.is_domain_controller = 0
            AND c.name IS NOT NULL
        ORDER BY 
            CASE 
                WHEN dw.warranty_end_date IS NULL THEN 3
                WHEN dw.warranty_end_date < GETDATE() THEN 1
                WHEN dw.warranty_end_date <= DATEADD(day, 30, GETDATE()) THEN 2
                ELSE 4
            END,
            dw.warranty_end_date ASC
        """
        
        logger.info('⚡ Executando query de garantias...')
        start_time = time.time()
        
        warranties = sql_manager.execute_query(query)
        
        query_time = time.time() - start_time
        logger.info(f'✅ Query executada em {query_time:.2f}s')
        
        if not warranties:
            logger.warning('⚠️ Nenhuma garantia encontrada na base de dados')
            return jsonify([])
        
        # Processar dados das garantias
        processed_warranties = []
        for row in warranties:
            warranty_data = {
                'computer_id': row['computer_id'],
                'computer_name': row['computer_name'],
                'warranty_status': row['warranty_status'],
                'warranty_start_date': row['warranty_start_date'].isoformat() if row['warranty_start_date'] else None,
                'warranty_end_date': row['warranty_end_date'].isoformat() if row['warranty_end_date'] else None,
                'last_updated': row['last_updated'].isoformat() if row['last_updated'] else None,
                'last_error': row['last_error'],
                'service_tag': row['service_tag'],
                'service_tag_clean': row['service_tag_clean'],
                'product_line_description': row['product_line_description'],
                'system_description': row['system_description'],
                'is_enabled': row['is_enabled'],
                'last_logon_timestamp': row['last_logon_timestamp'].isoformat() if row['last_logon_timestamp'] else None
            }
            processed_warranties.append(warranty_data)
        
        logger.info(f'✅ {len(processed_warranties)} garantias retornadas')
        
        return jsonify(processed_warranties)
        
    except Exception as e:
        logger.error(f'❌ Erro ao buscar garantias: {e}')
        
        # Em caso de erro, retornar array vazio para não quebrar o frontend
        return jsonify([]), 200

@app.route('/api/computers/warranty-stats', methods=['GET'])
def get_warranty_stats():
    """
    Retorna apenas estatísticas de garantias (mais rápido para dashboards)
    """
    try:
        logger.info('📊 Buscando estatísticas de garantias...')
        
        query = """
        SELECT 
            COUNT(*) as total,
            SUM(CASE 
                WHEN dw.warranty_status = 'Active' 
                    AND dw.warranty_end_date > GETDATE() 
                    AND dw.warranty_end_date > DATEADD(day, 60, GETDATE())
                THEN 1 ELSE 0 
            END) as active,
            SUM(CASE 
                WHEN dw.warranty_end_date < GETDATE() 
                THEN 1 ELSE 0 
            END) as expired,
            SUM(CASE 
                WHEN dw.warranty_end_date BETWEEN GETDATE() AND DATEADD(day, 30, GETDATE()) 
                THEN 1 ELSE 0 
            END) as expiring_30,
            SUM(CASE 
                WHEN dw.warranty_end_date BETWEEN DATEADD(day, 31, GETDATE()) AND DATEADD(day, 60, GETDATE()) 
                THEN 1 ELSE 0 
            END) as expiring_60,
            SUM(CASE 
                WHEN dw.warranty_end_date IS NULL OR dw.last_error IS NOT NULL 
                THEN 1 ELSE 0 
            END) as unknown
        FROM dell_warranty dw
        INNER JOIN computers c ON dw.computer_id = c.id
        WHERE c.is_domain_controller = 0
        """
        
        result = sql_manager.execute_query(query)
        
        if not result:
            # Retornar estatísticas zeradas se não há dados
            stats = {
                'total': 0,
                'active': 0,
                'expired': 0,
                'expiring_30': 0,
                'expiring_60': 0,
                'unknown': 0
            }
        else:
            stats = result[0]
        
        response_data = {
            'total': int(stats.get('total', 0)),
            'active': int(stats.get('active', 0)),
            'expired': int(stats.get('expired', 0)),
            'expiring_30': int(stats.get('expiring_30', 0)),
            'expiring_60': int(stats.get('expiring_60', 0)),
            'unknown': int(stats.get('unknown', 0)),
            'last_updated': datetime.now().isoformat()
        }
        
        logger.info(f'✅ Estatísticas calculadas: {response_data}')
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f'❌ Erro ao buscar estatísticas de garantias: {e}')
        
        # Retornar estatísticas zeradas em caso de erro
        return jsonify({
            'total': 0,
            'active': 0,
            'expired': 0,
            'expiring_30': 0,
            'expiring_60': 0,
            'unknown': 0,
            'last_updated': datetime.now().isoformat(),
            'error': 'Erro ao carregar estatísticas'
        })

@app.route('/api/computers/warranty/<int:computer_id>', methods=['GET'])
def get_warranty_by_computer_id(computer_id):
    """
    Retorna garantia específica de uma máquina por ID
    """
    try:
        logger.info(f'🔍 Buscando garantia para computer_id: {computer_id}')
        
        query = """
        SELECT 
            dw.*,
            c.name as computer_name,
            c.description as computer_description
        FROM dell_warranty dw
        INNER JOIN computers c ON dw.computer_id = c.id
        WHERE dw.computer_id = ?
        """
        
        result = sql_manager.execute_query(query, [computer_id])
        
        if not result:
            return jsonify({ 
                'error': 'Garantia não encontrada para esta máquina',
                'computer_id': computer_id 
            }), 404
        
        warranty = result[0]
        
        # Calcular status da garantia
        warranty_calculated_status = 'unknown'
        days_to_expiry = None
        
        if warranty['warranty_end_date'] and not warranty['last_error']:
            now = datetime.now()
            end_date = warranty['warranty_end_date']
            
            if isinstance(end_date, str):
                end_date = datetime.fromisoformat(end_date)
            
            days_to_expiry = (end_date - now).days
            
            if days_to_expiry < 0:
                warranty_calculated_status = 'expired'
            elif days_to_expiry <= 30:
                warranty_calculated_status = 'expiring_30'
            elif days_to_expiry <= 60:
                warranty_calculated_status = 'expiring_60'
            else:
                warranty_calculated_status = 'active'
        
        # Preparar resposta
        response_data = {
            'id': warranty['id'],
            'computer_id': warranty['computer_id'],
            'computer_name': warranty['computer_name'],
            'computer_description': warranty['computer_description'],
            'service_tag': warranty['service_tag'],
            'service_tag_clean': warranty['service_tag_clean'],
            'warranty_start_date': warranty['warranty_start_date'].isoformat() if warranty['warranty_start_date'] else None,
            'warranty_end_date': warranty['warranty_end_date'].isoformat() if warranty['warranty_end_date'] else None,
            'warranty_status': warranty['warranty_status'],
            'warranty_calculated_status': warranty_calculated_status,
            'days_to_expiry': days_to_expiry,
            'product_line_description': warranty['product_line_description'],
            'system_description': warranty['system_description'],
            'ship_date': warranty['ship_date'].isoformat() if warranty.get('ship_date') else None,
            'order_number': warranty['order_number'],
            'entitlements': warranty['entitlements'],
            'last_updated': warranty['last_updated'].isoformat() if warranty['last_updated'] else None,
            'cache_expires_at': warranty['cache_expires_at'].isoformat() if warranty['cache_expires_at'] else None,
            'last_error': warranty['last_error'],
            'created_at': warranty['created_at'].isoformat() if warranty['created_at'] else None
        }
        
        logger.info(f'✅ Garantia encontrada para {warranty["computer_name"]}')
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f'❌ Erro ao buscar garantia específica: {e}')
        return jsonify({ 
            'error': 'Erro interno do servidor',
            'details': str(e) 
        }), 500

@app.route('/api/computers/warranty/refresh', methods=['POST'])
def refresh_warranties():
    """
    Força atualização das garantias Dell (chama script Python de atualização)
    """
    try:
        data = request.get_json() or {}
        max_computers = data.get('max_computers')
        only_expired = data.get('only_expired', False)
        only_errors = data.get('only_errors', False)
        workers = data.get('workers', 5)
        
        logger.info('🔄 Iniciando atualização de garantias Dell...')
        logger.info(f'Parâmetros: max_computers={max_computers}, only_expired={only_expired}, only_errors={only_errors}, workers={workers}')
        
        # Aqui você pode implementar a chamada para o script Python de atualização
        # Por exemplo, usando subprocess para chamar o script dell_warranty_updater.py
        
        import subprocess
        import os
        
        # Construir comando para o script de atualização
        script_path = 'dell_warranty_updater.py'  # Ajustar caminho conforme necessário
        
        cmd = ['python', script_path]
        
        if max_computers:
            cmd.extend(['--max-computers', str(max_computers)])
        
        if only_expired:
            cmd.append('--only-expired')
        
        if only_errors:
            cmd.append('--only-errors')
        
        cmd.extend(['--workers', str(workers)])
        
        # Para desenvolvimento, simular resposta sem executar o script
        if os.getenv('FLASK_ENV') == 'development':
            logger.info('🧪 Modo desenvolvimento - simulando atualização de garantias')
            
            simulated_response = {
                'success': True,
                'message': 'Atualização de garantias iniciada em background (simulação)',
                'timestamp': datetime.now().isoformat(),
                'parameters': {
                    'max_computers': max_computers or 'all',
                    'only_expired': only_expired,
                    'only_errors': only_errors,
                    'workers': workers
                },
                'estimated_duration': '5-15 minutos',
                'note': 'Esta é uma simulação para desenvolvimento'
            }
            
            logger.info('✅ Atualização de garantias simulada')
            return jsonify(simulated_response)
        
        # Executar script real em produção
        try:
            # Executar em background sem bloquear a API
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            
            response_data = {
                'success': True,
                'message': 'Atualização de garantias iniciada em background',
                'timestamp': datetime.now().isoformat(),
                'process_id': process.pid,
                'parameters': {
                    'max_computers': max_computers or 'all',
                    'only_expired': only_expired,
                    'only_errors': only_errors,
                    'workers': workers
                },
                'command': ' '.join(cmd),
                'estimated_duration': '5-30 minutos dependendo da quantidade'
            }
            
            logger.info(f'✅ Processo de atualização iniciado com PID: {process.pid}')
            return jsonify(response_data)
            
        except FileNotFoundError:
            logger.error('❌ Script de atualização de garantias não encontrado')
            return jsonify({
                'success': False,
                'message': 'Script de atualização não encontrado',
                'error': f'Arquivo {script_path} não encontrado',
                'timestamp': datetime.now().isoformat()
            }), 500
            
        except Exception as subprocess_error:
            logger.error(f'❌ Erro ao executar script de atualização: {subprocess_error}')
            return jsonify({
                'success': False,
                'message': 'Erro ao iniciar atualização de garantias',
                'error': str(subprocess_error),
                'timestamp': datetime.now().isoformat()
            }), 500
        
    except Exception as e:
        logger.error(f'❌ Erro ao iniciar atualização de garantias: {e}')
        return jsonify({ 
            'success': False,
            'message': 'Erro ao iniciar atualização de garantias',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/computers/warranty/refresh-status', methods=['GET'])
def get_warranty_refresh_status():
    """
    Retorna status da última atualização de garantias
    """
    try:
        # Buscar logs da última execução do script de garantias
        query = """
        SELECT TOP 5
            sync_type,
            start_time,
            end_time,
            status,
            computers_found,
            computers_added,
            computers_updated,
            errors_count,
            error_message
        FROM sync_logs
        WHERE sync_type LIKE '%warranty%' OR sync_type LIKE '%dell%'
        ORDER BY start_time DESC
        """
        
        logs = sql_manager.execute_query(query)
        
        # Status básico
        if logs:
            last_log = logs[0]
            last_run = {
                'type': last_log['sync_type'],
                'start_time': last_log['start_time'].isoformat() if last_log['start_time'] else None,
                'end_time': last_log['end_time'].isoformat() if last_log['end_time'] else None,
                'status': last_log['status'],
                'computers_found': last_log['computers_found'],
                'computers_updated': last_log['computers_updated'],
                'errors_count': last_log['errors_count'],
                'error_message': last_log['error_message']
            }
        else:
            last_run = None
        
        # Verificar se há processos rodando
        running_processes = []
        try:
            import psutil
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if 'dell_warranty' in ' '.join(proc.info['cmdline'] or []):
                        running_processes.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'cmdline': ' '.join(proc.info['cmdline'] or [])
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except ImportError:
            # psutil não disponível
            pass
        
        response_data = {
            'last_run': last_run,
            'running_processes': running_processes,
            'is_running': len(running_processes) > 0,
            'recent_logs': logs,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f'❌ Erro ao buscar status de atualização de garantias: {e}')
        return jsonify({
            'error': 'Erro interno do servidor',
            'details': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/computers/warranty/search', methods=['GET'])
def search_warranties():
    """
    Busca garantias com filtros específicos
    """
    try:
        # Parâmetros de busca
        status_filter = request.args.get('status', 'all')  # all, active, expired, expiring_30, expiring_60
        organization = request.args.get('organization', '')
        search_term = request.args.get('q', '')
        limit = min(int(request.args.get('limit', 100)), 1000)
        offset = int(request.args.get('offset', 0))
        
        logger.info(f'🔍 Buscando garantias com filtros: status={status_filter}, org={organization}, q={search_term}')
        
        # Construir WHERE clause baseado nos filtros
        where_conditions = ["c.is_domain_controller = 0"]
        params = []
        
        # Filtro de texto
        if search_term:
            where_conditions.append("""
                (c.name LIKE ? OR 
                 dw.service_tag LIKE ? OR 
                 dw.service_tag_clean LIKE ? OR
                 dw.product_line_description LIKE ? OR
                 dw.system_description LIKE ?)
            """)
            search_pattern = f"%{search_term}%"
            params.extend([search_pattern] * 5)
        
        # Filtro de organização
        if organization:
            where_conditions.append("o.code = ?")
            params.append(organization)
        
        # Filtro de status de garantia
        if status_filter != 'all':
            if status_filter == 'active':
                where_conditions.append("""
                    dw.warranty_end_date > GETDATE() 
                    AND dw.warranty_end_date > DATEADD(day, 60, GETDATE())
                    AND dw.last_error IS NULL
                """)
            elif status_filter == 'expired':
                where_conditions.append("dw.warranty_end_date < GETDATE()")
            elif status_filter == 'expiring_30':
                where_conditions.append("""
                    dw.warranty_end_date BETWEEN GETDATE() AND DATEADD(day, 30, GETDATE())
                """)
            elif status_filter == 'expiring_60':
                where_conditions.append("""
                    dw.warranty_end_date BETWEEN DATEADD(day, 31, GETDATE()) AND DATEADD(day, 60, GETDATE())
                """)
            elif status_filter == 'unknown':
                where_conditions.append("""
                    (dw.warranty_end_date IS NULL OR dw.last_error IS NOT NULL)
                """)
        
        where_clause = " AND ".join(where_conditions)
        
        # Query principal
        query = f"""
        SELECT 
            dw.computer_id,
            c.name as computer_name,
            dw.service_tag,
            dw.service_tag_clean,
            dw.warranty_start_date,
            dw.warranty_end_date,
            dw.warranty_status,
            dw.product_line_description,
            dw.system_description,
            dw.last_updated,
            dw.last_error,
            o.name as organization_name,
            o.code as organization_code,
            c.is_enabled
        FROM dell_warranty dw
        INNER JOIN computers c ON dw.computer_id = c.id
        LEFT JOIN organizations o ON c.organization_id = o.id
        WHERE {where_clause}
        ORDER BY 
            CASE 
                WHEN dw.warranty_end_date IS NULL THEN 3
                WHEN dw.warranty_end_date < GETDATE() THEN 1
                WHEN dw.warranty_end_date <= DATEADD(day, 30, GETDATE()) THEN 2
                ELSE 4
            END,
            dw.warranty_end_date ASC,
            c.name
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """
        
        # Query de contagem
        count_query = f"""
        SELECT COUNT(*) as total
        FROM dell_warranty dw
        INNER JOIN computers c ON dw.computer_id = c.id
        LEFT JOIN organizations o ON c.organization_id = o.id
        WHERE {where_clause}
        """
        
        # Executar queries
        params_with_pagination = params + [offset, limit]
        results = sql_manager.execute_query(query, params_with_pagination)
        count_result = sql_manager.execute_query(count_query, params)
        
        total = count_result[0]['total'] if count_result else 0
        
        # Processar resultados
        warranties = []
        for row in results:
            warranty_data = {
                'computer_id': row['computer_id'],
                'computer_name': row['computer_name'],
                'service_tag': row['service_tag'],
                'service_tag_clean': row['service_tag_clean'],
                'warranty_start_date': row['warranty_start_date'].isoformat() if row['warranty_start_date'] else None,
                'warranty_end_date': row['warranty_end_date'].isoformat() if row['warranty_end_date'] else None,
                'warranty_status': row['warranty_status'],
                'product_line_description': row['product_line_description'],
                'system_description': row['system_description'],
                'last_updated': row['last_updated'].isoformat() if row['last_updated'] else None,
                'last_error': row['last_error'],
                'organization_name': row['organization_name'],
                'organization_code': row['organization_code'],
                'is_enabled': row['is_enabled']
            }
            warranties.append(warranty_data)
        
        response_data = {
            'warranties': warranties,
            'total': total,
            'limit': limit,
            'offset': offset,
            'has_more': (offset + limit) < total,
            'filters': {
                'status': status_filter,
                'organization': organization,
                'search_term': search_term
            },
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f'✅ Busca de garantias retornou {len(warranties)} de {total} resultados')
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f'❌ Erro na busca de garantias: {e}')
        return jsonify({
            'error': 'Erro interno do servidor',
            'details': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# =============================================================================
# FUNÇÃO AUXILIAR PARA INTEGRAÇÃO COM O SCRIPT DE ATUALIZAÇÃO
# =============================================================================

def log_warranty_sync_operation(sync_type, status, stats=None, error_message=None):
    """
    Função auxiliar para o script de atualização de garantias registrar operações
    """
    try:
        query = """
        INSERT INTO sync_logs (
            sync_type, start_time, end_time, status,
            computers_found, computers_added, computers_updated, 
            errors_count, error_message, triggered_by
        ) VALUES (?, GETDATE(), GETDATE(), ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            sync_type,
            status,
            stats.get('found', 0) if stats else 0,
            stats.get('added', 0) if stats else 0,
            stats.get('updated', 0) if stats else 0,
            stats.get('errors', 0) if stats else 0,
            error_message,
            'dell_warranty_script'
        )
        
        sql_manager.execute_query(query, params, fetch=False)
        logger.info(f'📝 Log de sincronização de garantias registrado: {sync_type} - {status}')
        
    except Exception as e:
        logger.error(f'❌ Erro ao registrar log de sincronização de garantias: {e}')

# =============================================================================
# ENDPOINT PARA DEBUGGING DE GARANTIAS
# =============================================================================

@app.route('/api/computers/warranty/debug/<computer_name>', methods=['GET'])
def debug_warranty_info(computer_name):
    """
    Endpoint de debug para verificar informações de garantia de uma máquina específica
    """
    try:
        debug_info = {
            'computer_name': computer_name,
            'timestamp': datetime.now().isoformat(),
            'tests': {}
        }
        
        # 1. Verificar se computador existe no banco
        logger.info(f'🔍 Debug garantia - Verificando computador {computer_name}')
        
        computer_query = """
        SELECT id, name, description, organization_id 
        FROM computers 
        WHERE name = ? AND is_domain_controller = 0
        """
        
        computer_result = sql_manager.execute_query(computer_query, [computer_name])
        
        if computer_result:
            computer = computer_result[0]
            debug_info['tests']['computer_exists'] = {
                'found': True,
                'computer_id': computer['id'],
                'description': computer['description']
            }
            
            # 2. Verificar se tem dados de garantia
            warranty_query = """
            SELECT * FROM dell_warranty WHERE computer_id = ?
            """
            
            warranty_result = sql_manager.execute_query(warranty_query, [computer['id']])
            
            if warranty_result:
                warranty = warranty_result[0]
                debug_info['tests']['warranty_exists'] = {
                    'found': True,
                    'service_tag': warranty['service_tag'],
                    'warranty_status': warranty['warranty_status'],
                    'warranty_end_date': warranty['warranty_end_date'].isoformat() if warranty['warranty_end_date'] else None,
                    'last_updated': warranty['last_updated'].isoformat() if warranty['last_updated'] else None,
                    'last_error': warranty['last_error']
                }
            else:
                debug_info['tests']['warranty_exists'] = {
                    'found': False,
                    'message': 'Nenhum dado de garantia encontrado'
                }
            
            # 3. Tentar extrair service tag do nome
            extracted_service_tag = extract_service_tag_from_computer_name(computer_name)
            debug_info['tests']['service_tag_extraction'] = {
                'original_name': computer_name,
                'extracted_service_tag': extracted_service_tag,
                'extraction_successful': extracted_service_tag != computer_name
            }
            
            # 4. Teste da API Dell com a service tag extraída
            if extracted_service_tag:
                logger.info(f'🔍 Debug garantia - Testando API Dell para {extracted_service_tag}')
                
                try:
                    dell_result = dell_api.get_warranty_info(extracted_service_tag)
                    
                    debug_info['tests']['dell_api_test'] = {
                        'attempted': True,
                        'service_tag_used': extracted_service_tag,
                        'success': 'error' not in dell_result,
                        'result': dell_result
                    }
                except Exception as dell_error:
                    debug_info['tests']['dell_api_test'] = {
                        'attempted': True,
                        'service_tag_used': extracted_service_tag,
                        'success': False,
                        'error': str(dell_error)
                    }
            else:
                debug_info['tests']['dell_api_test'] = {
                    'attempted': False,
                    'reason': 'Não foi possível extrair service tag válida'
                }
        else:
            debug_info['tests']['computer_exists'] = {
                'found': False,
                'message': f'Computador {computer_name} não encontrado na base de dados'
            }
        
        # 5. Resumo e recomendações
        debug_info['summary'] = {
            'computer_in_db': debug_info['tests']['computer_exists']['found'],
            'has_warranty_data': debug_info['tests'].get('warranty_exists', {}).get('found', False),
            'can_extract_service_tag': debug_info['tests'].get('service_tag_extraction', {}).get('extraction_successful', False),
            'dell_api_working': debug_info['tests'].get('dell_api_test', {}).get('success', False)
        }
        
        # Recomendações
        recommendations = []
        
        if not debug_info['summary']['computer_in_db']:
            recommendations.append('Computador não encontrado - verificar se está sincronizado do AD')
        
        if not debug_info['summary']['has_warranty_data']:
            recommendations.append('Executar script de atualização de garantias Dell')
        
        if not debug_info['summary']['can_extract_service_tag']:
            recommendations.append('Verificar se nome do computador segue padrão com service tag')
        
        if not debug_info['summary']['dell_api_working']:
            recommendations.append('Verificar conectividade com API Dell e credenciais')
        
        if debug_info['tests'].get('warranty_exists', {}).get('found') and debug_info['tests']['warranty_exists'].get('last_error'):
            recommendations.append('Executar atualização específica para corrigir erro na garantia')
        
        debug_info['summary']['recommendations'] = recommendations
        
        return jsonify(debug_info), 200
        
    except Exception as e:
        logger.error(f'❌ Erro no debug de garantia para {computer_name}: {e}')
        return jsonify({
            'success': False,
            'computer_name': computer_name,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# =============================================================================
# ENDPOINT PARA ATUALIZAR GARANTIA DE UMA MÁQUINA ESPECÍFICA
# =============================================================================

@app.route('/api/computers/<computer_name>/warranty/refresh', methods=['POST'])
def refresh_single_computer_warranty(computer_name):
    """
    Atualiza garantia de uma máquina específica
    """
    try:
        logger.info(f'🔄 Atualizando garantia individual para {computer_name}')
        
        # 1. Verificar se computador existe
        computer_query = """
        SELECT id, name, description 
        FROM computers 
        WHERE name = ? AND is_domain_controller = 0
        """
        
        computer_result = sql_manager.execute_query(computer_query, [computer_name])
        
        if not computer_result:
            return jsonify({
                'success': False,
                'message': f'Computador {computer_name} não encontrado',
                'computer_name': computer_name
            }), 404
        
        computer = computer_result[0]
        computer_id = computer['id']
        
        # 2. Extrair service tag
        service_tag = extract_service_tag_from_computer_name(computer_name)
        
        if not service_tag or len(service_tag) < 5:
            return jsonify({
                'success': False,
                'message': f'Não foi possível extrair service tag válida de {computer_name}',
                'computer_name': computer_name,
                'extracted_service_tag': service_tag
            }), 400
        
        # 3. Consultar API Dell
        logger.info(f'🔍 Consultando API Dell para service tag: {service_tag}')
        warranty_data = dell_api.get_warranty_info(service_tag)
        
        if 'error' in warranty_data:
            # Salvar erro no banco
            error_query = """
            MERGE dell_warranty AS target
            USING (SELECT ? as computer_id) AS source
            ON target.computer_id = source.computer_id
            WHEN MATCHED THEN
                UPDATE SET 
                    service_tag = ?,
                    last_updated = GETDATE(),
                    cache_expires_at = DATEADD(hour, 6, GETDATE()),
                    last_error = ?
            WHEN NOT MATCHED THEN
                INSERT (computer_id, service_tag, last_updated, cache_expires_at, last_error, created_at)
                VALUES (?, ?, GETDATE(), DATEADD(hour, 6, GETDATE()), ?, GETDATE());
            """
            
            error_message = f"{warranty_data.get('code', 'ERROR')}: {warranty_data.get('error', 'Unknown error')}"
            
            sql_manager.execute_query(error_query, [
                computer_id, service_tag, error_message,
                computer_id, service_tag, error_message
            ], fetch=False)
            
            return jsonify({
                'success': False,
                'message': f'Erro ao consultar garantia: {warranty_data["error"]}',
                'computer_name': computer_name,
                'service_tag': service_tag,
                'error_code': warranty_data.get('code'),
                'dell_api_error': warranty_data['error']
            }), 200
        
        # 4. Processar dados de garantia bem-sucedidos
        warranty_start_date = None
        warranty_end_date = None
        warranty_status = 'Unknown'
        
        # Processar datas se existirem
        if warranty_data.get('dataExpiracao') and warranty_data['dataExpiracao'] != 'Não disponível':
            try:
                # Converter data de DD/MM/YYYY para datetime
                from datetime import datetime as dt
                warranty_end_date = dt.strptime(warranty_data['dataExpiracao'], '%d/%m/%Y')
                warranty_status = 'Active' if warranty_data.get('status') == 'Em garantia' else 'Expired'
            except:
                pass
        
        # 5. Salvar dados no banco
        upsert_query = """
        MERGE dell_warranty AS target
        USING (SELECT ? as computer_id) AS source
        ON target.computer_id = source.computer_id
        WHEN MATCHED THEN
            UPDATE SET 
                service_tag = ?,
                service_tag_clean = ?,
                warranty_start_date = ?,
                warranty_end_date = ?,
                warranty_status = ?,
                product_line_description = ?,
                system_description = ?,
                last_updated = GETDATE(),
                cache_expires_at = DATEADD(day, 7, GETDATE()),
                last_error = NULL
        WHEN NOT MATCHED THEN
            INSERT (computer_id, service_tag, service_tag_clean, warranty_start_date, warranty_end_date,
                   warranty_status, product_line_description, system_description, 
                   last_updated, cache_expires_at, last_error, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, GETDATE(), DATEADD(day, 7, GETDATE()), NULL, GETDATE());
        """
        
        params = [
            computer_id, service_tag, service_tag, warranty_start_date, warranty_end_date,
            warranty_status, warranty_data.get('modelo', ''), warranty_data.get('modelo', ''),
            computer_id, service_tag, service_tag, warranty_start_date, warranty_end_date,
            warranty_status, warranty_data.get('modelo', ''), warranty_data.get('modelo', '')
        ]
        
        sql_manager.execute_query(upsert_query, params, fetch=False)
        
        # 6. Preparar resposta de sucesso
        response_data = {
            'success': True,
            'message': f'Garantia atualizada com sucesso para {computer_name}',
            'computer_name': computer_name,
            'computer_id': computer_id,
            'service_tag': service_tag,
            'warranty_data': {
                'service_tag': service_tag,
                'warranty_status': warranty_status,
                'warranty_end_date': warranty_end_date.isoformat() if warranty_end_date else None,
                'product_description': warranty_data.get('modelo', ''),
                'dell_status': warranty_data.get('status', ''),
                'expiration_date_formatted': warranty_data.get('dataExpiracao', ''),
                'ship_date': warranty_data.get('shipDate'),
                'order_number': warranty_data.get('orderNumber')
            },
            'last_updated': datetime.now().isoformat(),
            'cache_expires_in_days': 7
        }
        
        logger.info(f'✅ Garantia atualizada para {computer_name}: {warranty_status} - {warranty_data.get("dataExpiracao", "N/A")}')
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f'❌ Erro ao atualizar garantia individual para {computer_name}: {e}')
        return jsonify({
            'success': False,
            'message': f'Erro interno ao atualizar garantia: {str(e)}',
            'computer_name': computer_name,
            'timestamp': datetime.now().isoformat()
        }), 500

# =============================================================================
# ENDPOINT PARA EXPORTAR DADOS DE GARANTIA
# =============================================================================

@app.route('/api/computers/warranty/export', methods=['GET'])
def export_warranty_data():
    """
    Exporta dados de garantia em formato CSV
    """
    try:
        format_type = request.args.get('format', 'csv').lower()
        status_filter = request.args.get('status', 'all')
        
        logger.info(f'📤 Exportando dados de garantia em formato {format_type}')
        
        # Query para exportação
        query = """
        SELECT 
            c.name as computer_name,
            dw.service_tag,
            dw.service_tag_clean,
            dw.warranty_status,
            dw.warranty_start_date,
            dw.warranty_end_date,
            dw.product_line_description,
            dw.system_description,
            dw.last_updated,
            dw.last_error,
            o.name as organization_name,
            o.code as organization_code,
            c.is_enabled,
            c.last_logon_timestamp,
            CASE 
                WHEN dw.warranty_end_date IS NULL THEN 'Desconhecido'
                WHEN dw.warranty_end_date < GETDATE() THEN 'Expirada'
                WHEN dw.warranty_end_date <= DATEADD(day, 30, GETDATE()) THEN 'Expirando em 30 dias'
                WHEN dw.warranty_end_date <= DATEADD(day, 60, GETDATE()) THEN 'Expirando em 60 dias'
                ELSE 'Ativa'
            END as warranty_status_calc,
            CASE 
                WHEN dw.warranty_end_date IS NOT NULL AND dw.warranty_end_date >= GETDATE()
                THEN DATEDIFF(day, GETDATE(), dw.warranty_end_date)
                ELSE NULL
            END as days_to_expiry
        FROM dell_warranty dw
        INNER JOIN computers c ON dw.computer_id = c.id
        LEFT JOIN organizations o ON c.organization_id = o.id
        WHERE c.is_domain_controller = 0
        """
        
        # Aplicar filtro de status se especificado
        params = []
        if status_filter != 'all':
            if status_filter == 'active':
                query += " AND dw.warranty_end_date > DATEADD(day, 60, GETDATE())"
            elif status_filter == 'expired':
                query += " AND dw.warranty_end_date < GETDATE()"
            elif status_filter == 'expiring_30':
                query += " AND dw.warranty_end_date BETWEEN GETDATE() AND DATEADD(day, 30, GETDATE())"
            elif status_filter == 'expiring_60':
                query += " AND dw.warranty_end_date BETWEEN DATEADD(day, 31, GETDATE()) AND DATEADD(day, 60, GETDATE())"
        
        query += " ORDER BY dw.warranty_end_date ASC, c.name"
        
        results = sql_manager.execute_query(query, params)
        
        if format_type == 'csv':
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Cabeçalhos
            headers = [
                'Computer Name', 'Service Tag', 'Service Tag Clean', 'Warranty Status',
                'Warranty Start Date', 'Warranty End Date', 'Product Description',
                'System Description', 'Last Updated', 'Organization', 'Organization Code',
                'Computer Enabled', 'Last Logon', 'Warranty Status Calculated', 'Days to Expiry',
                'Last Error'
            ]
            writer.writerow(headers)
            
            # Dados
            for row in results:
                csv_row = [
                    row['computer_name'],
                    row['service_tag'] or '',
                    row['service_tag_clean'] or '',
                    row['warranty_status'] or '',
                    row['warranty_start_date'].strftime('%Y-%m-%d') if row['warranty_start_date'] else '',
                    row['warranty_end_date'].strftime('%Y-%m-%d') if row['warranty_end_date'] else '',
                    row['product_line_description'] or '',
                    row['system_description'] or '',
                    row['last_updated'].strftime('%Y-%m-%d %H:%M:%S') if row['last_updated'] else '',
                    row['organization_name'] or '',
                    row['organization_code'] or '',
                    'Yes' if row['is_enabled'] else 'No',
                    row['last_logon_timestamp'].strftime('%Y-%m-%d %H:%M:%S') if row['last_logon_timestamp'] else '',
                    row['warranty_status_calc'],
                    row['days_to_expiry'] if row['days_to_expiry'] is not None else '',
                    row['last_error'] or ''
                ]
                writer.writerow(csv_row)
            
            output.seek(0)
            csv_content = output.getvalue()
            output.close()
            
            # Retornar CSV como download
            from flask import Response
            
            filename = f"dell_warranties_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            return Response(
                csv_content,
                mimetype='text/csv',
                headers={"Content-disposition": f"attachment; filename={filename}"}
            )
            
        elif format_type == 'json':
            # Processar dados para JSON
            processed_results = []
            for row in results:
                processed_row = {
                    'computer_name': row['computer_name'],
                    'service_tag': row['service_tag'],
                    'service_tag_clean': row['service_tag_clean'],
                    'warranty_status': row['warranty_status'],
                    'warranty_start_date': row['warranty_start_date'].isoformat() if row['warranty_start_date'] else None,
                    'warranty_end_date': row['warranty_end_date'].isoformat() if row['warranty_end_date'] else None,
                    'product_line_description': row['product_line_description'],
                    'system_description': row['system_description'],
                    'last_updated': row['last_updated'].isoformat() if row['last_updated'] else None,
                    'organization_name': row['organization_name'],
                    'organization_code': row['organization_code'],
                    'is_enabled': row['is_enabled'],
                    'last_logon_timestamp': row['last_logon_timestamp'].isoformat() if row['last_logon_timestamp'] else None,
                    'warranty_status_calculated': row['warranty_status_calc'],
                    'days_to_expiry': row['days_to_expiry'],
                    'last_error': row['last_error']
                }
                processed_results.append(processed_row)
            
            return jsonify({
                'success': True,
                'data': processed_results,
                'total_records': len(processed_results),
                'export_date': datetime.now().isoformat(),
                'status_filter': status_filter
            })
        
        else:
            return jsonify({
                'success': False,
                'message': f'Formato {format_type} não suportado. Use csv ou json.'
            }), 400
        
    except Exception as e:
        logger.error(f'❌ Erro ao exportar dados de garantia: {e}')
        return jsonify({
            'success': False,
            'message': f'Erro ao exportar dados: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

# compatibility route removed - using single-machine refresh endpoints

@app.route('/api/computers/sync-complete', methods=['POST'])
def sync_complete_from_ad():
    """
    Sincronização completa AD → SQL (limpeza total e recriação)
    Remove TODAS as máquinas antigas e recria com dados atuais do AD
    """
    try:
        logger.info('🔄 Iniciando sincronização completa AD → SQL com limpeza total')
        
        # 1. Buscar TODAS as máquinas do AD
        logger.info('📡 Buscando máquinas do Active Directory...')
        ad_computers = ad_manager.get_computers()
        
        if not ad_computers:
            return jsonify({
                'success': False,
                'message': 'Nenhuma máquina encontrada no Active Directory',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        logger.info(f'📊 {len(ad_computers)} máquinas encontradas no AD')
        
        # 2. Obter estatísticas antes da limpeza
        stats_before_query = """
        SELECT 
            COUNT(*) as total_before,
            SUM(CASE WHEN is_enabled = 1 THEN 1 ELSE 0 END) as enabled_before,
            SUM(CASE WHEN is_enabled = 0 THEN 1 ELSE 0 END) as disabled_before
        FROM computers 
        WHERE is_domain_controller = 0
        """
        
        stats_before_result = sql_manager.execute_query(stats_before_query)
        stats_before = stats_before_result[0] if stats_before_result else {}
        
        logger.info(f'📊 Estado antes da limpeza: {stats_before.get("total_before", 0)} máquinas')
        
        # 3. LIMPEZA COMPLETA - Deletar todas as máquinas não-DC
        logger.info('🗑️ Removendo TODAS as máquinas antigas do SQL...')
        
        cleanup_query = """
        DELETE FROM computers 
        WHERE is_domain_controller = 0
        """
        
        deleted_count = sql_manager.execute_query(cleanup_query, fetch=False)
        logger.info(f'✅ {deleted_count} máquinas antigas removidas do SQL')
        
        # 4. Limpar também dados relacionados se existirem
        try:
            # Limpar logs antigos de operações de computadores
            cleanup_logs_query = """
            DELETE FROM computer_operations_log 
            WHERE operation_time < DATEADD(day, -30, GETDATE())
            """
            sql_manager.execute_query(cleanup_logs_query, fetch=False)
            
            # Limpar dados de garantia órfãos se a tabela existir
            cleanup_warranty_query = """
            IF EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'dell_warranty')
            BEGIN
                DELETE FROM dell_warranty 
                WHERE computer_id NOT IN (SELECT id FROM computers)
            END
            """
            sql_manager.execute_query(cleanup_warranty_query, fetch=False)
            
        except Exception as cleanup_error:
            logger.warning(f'⚠️ Erro na limpeza de dados relacionados (não crítico): {cleanup_error}')
        
        # 5. Inserir TODAS as máquinas do AD
        logger.info('📥 Inserindo máquinas atuais do AD...')
        
        stats = {
            'found_ad': len(ad_computers),
            'total_before': stats_before.get('total_before', 0),
            'deleted': deleted_count,
            'added': 0,
            'updated': 0,
            'errors': 0
        }
        
        for computer in ad_computers:
            try:
                # Usar função de sincronização que agora vai inserir como novo
                result = sql_manager.sync_computer_to_sql(computer)
                
                if result:
                    stats['added'] += 1
                else:
                    stats['errors'] += 1
                    logger.warning(f'⚠️ Falha ao inserir {computer.get("name", "Unknown")}')
                    
            except Exception as e:
                logger.error(f'❌ Erro ao inserir {computer.get("name", "Unknown")}: {e}')
                stats['errors'] += 1
        
        # 6. Verificar resultado final
        final_stats_query = """
        SELECT 
            COUNT(*) as total_after,
            SUM(CASE WHEN is_enabled = 1 THEN 1 ELSE 0 END) as enabled_after,
            SUM(CASE WHEN is_enabled = 0 THEN 1 ELSE 0 END) as disabled_after
        FROM computers 
        WHERE is_domain_controller = 0
        """
        
        final_stats_result = sql_manager.execute_query(final_stats_query)
        final_stats = final_stats_result[0] if final_stats_result else {}
        
        stats['total_after'] = final_stats.get('total_after', 0)
        stats['enabled_after'] = final_stats.get('enabled_after', 0)
        stats['disabled_after'] = final_stats.get('disabled_after', 0)
        
        # 7. Registrar operação de sincronização
        sql_manager.log_sync_operation(
            'complete_sync_with_cleanup', 
            'completed' if stats['errors'] == 0 else 'completed_with_errors', 
            {
                'found': stats['found_ad'],
                'added': stats['added'], 
                'updated': 0,  # Não há updates numa limpeza completa
                'errors': stats['errors']
            }
        )
        
        # 8. Resetar IDs se necessário (opcional - para reorganizar)
        try:
            reset_identity_query = """
            IF EXISTS (SELECT * FROM computers WHERE is_domain_controller = 0)
            BEGIN
                DECLARE @max_id INT
                SELECT @max_id = ISNULL(MAX(id), 0) FROM computers
                DBCC CHECKIDENT('computers', RESEED, @max_id)
            END
            """
            sql_manager.execute_query(reset_identity_query, fetch=False)
        except Exception as reset_error:
            logger.warning(f'⚠️ Erro ao resetar identities (não crítico): {reset_error}')
        
        duration_message = f"Sincronização completa com limpeza finalizada"
        
        response_data = {
            'success': True,
            'message': duration_message,
            'stats': {
                'computers_found_ad': stats['found_ad'],
                'computers_before_cleanup': stats['total_before'],
                'computers_deleted': stats['deleted'],
                'computers_added': stats['added'],
                'computers_after_sync': stats['total_after'],
                'enabled_after': stats['enabled_after'],
                'disabled_after': stats['disabled_after'],
                'computers_with_errors': stats['errors'],
                'total_processed': stats['found_ad']
            },
            'operation_type': 'complete_cleanup_and_rebuild',
            'timestamp': datetime.now().isoformat(),
            'cache_cleared': True,
            'data_refreshed': True
        }
        
        logger.info(f'✅ Sincronização completa com limpeza concluída: {stats}')
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f'❌ Erro na sincronização completa com limpeza: {e}')
        
        # Registrar erro
        sql_manager.log_sync_operation(
            'complete_sync_with_cleanup', 
            'failed', 
            error_message=str(e)
        )
        
        return jsonify({
            'success': False,
            'message': f'Erro na sincronização completa: {str(e)}',
            'operation_type': 'complete_cleanup_and_rebuild',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/computers/sync-incremental', methods=['POST'])
def sync_incremental_from_ad():
    """
    Sincronização incremental tradicional (apenas adiciona/atualiza)
    Mantém máquinas existentes e apenas atualiza dados
    """
    try:
        logger.info('🔄 Iniciando sincronização incremental AD → SQL')
        
        # Usar a função de sincronização tradicional
        sync_service.sync_ad_to_sql()
        
        return jsonify({
            'success': True,
            'message': 'Sincronização incremental concluída',
            'operation_type': 'incremental_update',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f'❌ Erro na sincronização incremental: {e}')
        return jsonify({
            'success': False,
            'message': f'Erro na sincronização incremental: {str(e)}',
            'operation_type': 'incremental_update',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/computers/force-ad-refresh', methods=['POST'])
def force_ad_refresh():
    """
    Força uma busca direta no AD e sincronização completa com limpeza
    """
    try:
        logger.info('🔄 Forçando refresh completo do AD com limpeza')
        
        # Chamar a sincronização completa com limpeza
        return sync_complete_from_ad()
        
    except Exception as e:
        logger.error(f'❌ Erro no refresh forçado do AD: {e}')
        return jsonify({
            'success': False,
            'message': f'Erro no refresh do AD: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

# Adicionar também uma rota para verificar status
@app.route('/api/computers/sync-status', methods=['GET'])
def get_detailed_sync_status():
    """
    Retorna status detalhado da sincronização e diferenças AD vs SQL
    """
    try:
        # Stats do SQL atual
        sql_stats_query = """
        SELECT 
            COUNT(*) as total_sql,
            SUM(CASE WHEN is_enabled = 1 THEN 1 ELSE 0 END) as enabled_sql,
            SUM(CASE WHEN is_enabled = 0 THEN 1 ELSE 0 END) as disabled_sql,
            MAX(last_sync_ad) as last_sync_time,
            COUNT(CASE WHEN last_sync_ad IS NULL THEN 1 END) as never_synced,
            COUNT(CASE WHEN last_sync_ad < DATEADD(hour, -24, GETDATE()) THEN 1 END) as outdated_sync
        FROM computers 
        WHERE is_domain_controller = 0
        """
        
        sql_stats_result = sql_manager.execute_query(sql_stats_query)
        sql_stats = sql_stats_result[0] if sql_stats_result else {}
        
        # Tentar obter stats do AD (pode ser lento)
        try:
            ad_computers = ad_manager.get_computers()
            ad_stats = {
                'total_ad': len(ad_computers),
                'enabled_ad': len([c for c in ad_computers if not c.get('disabled', False)]),
                'disabled_ad': len([c for c in ad_computers if c.get('disabled', False)])
            }
        except Exception as ad_error:
            logger.warning(f'⚠️ Erro ao obter stats do AD: {ad_error}')
            ad_stats = {
                'total_ad': 0,
                'enabled_ad': 0,
                'disabled_ad': 0,
                'ad_error': str(ad_error)
            }
        
        # Últimos logs de sincronização
        recent_logs_query = """
        SELECT TOP 5
            sync_type,
            start_time,
            end_time,
            status,
            computers_found,
            computers_added,
            computers_updated,
            errors_count,
            error_message
        FROM sync_logs
        ORDER BY start_time DESC
        """
        
        recent_logs = sql_manager.execute_query(recent_logs_query)
        
        response_data = {
            'sql_stats': sql_stats,
            'ad_stats': ad_stats,
            'sync_needed': (sql_stats.get('total_sql', 0) != ad_stats.get('total_ad', 0)),
            'sync_service_status': {
                'running': sync_service.sync_running,
                'last_sync': sync_service.last_sync.isoformat() if sync_service.last_sync else None
            },
            'recent_sync_logs': recent_logs,
            'recommendations': [],
            'timestamp': datetime.now().isoformat()
        }
        
        # Adicionar recomendações
        if sql_stats.get('total_sql', 0) == 0:
            response_data['recommendations'].append('Executar sincronização completa - SQL vazio')
        elif sql_stats.get('total_sql', 0) != ad_stats.get('total_ad', 0):
            response_data['recommendations'].append('Diferença detectada entre AD e SQL - considerar sincronização completa')
        elif sql_stats.get('never_synced', 0) > 0:
            response_data['recommendations'].append(f'{sql_stats.get("never_synced")} máquinas nunca sincronizadas')
        elif sql_stats.get('outdated_sync', 0) > 0:
            response_data['recommendations'].append(f'{sql_stats.get("outdated_sync")} máquinas com sync antigo (24h+)')
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f'❌ Erro ao obter status de sincronização: {e}')
        return jsonify({
            'error': 'Erro interno do servidor',
            'details': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500
if __name__ == '__main__':
    print("🚀 Iniciando API AD Computer Manager")
    print(f"📊 SQL Server: {SQL_SERVER}/{SQL_DATABASE}")
    print(f"🔗 Active Directory: {AD_SERVER}")
    print(f"🌐 Porta: 42057")
    print("=" * 60)
    
    # Testar conexões iniciais
    try:
        print("🔍 Testando conexão SQL Server...")
        test_result = sql_manager.execute_query("SELECT COUNT(*) as total FROM computers WHERE is_domain_controller = 0")
        computer_count = test_result[0]['total'] if test_result else 0
        print(f"✅ SQL OK - {computer_count} computadores encontrados")
    except Exception as e:
        print(f"❌ Erro SQL: {e}")
    
    try:
        print("🔍 Testando conexão Active Directory...")
        if ad_manager.connect():
            print("✅ Active Directory OK")
            ad_manager.connection.unbind()
        else:
            print("❌ Falha na conexão AD")
    except Exception as e:
        print(f"❌ Erro AD: {e}")
    
    # Iniciar serviço de sincronização em background
    try:
        print("🔄 Iniciando serviço de sincronização...")
        sync_service.start_background_sync()
        print("✅ Serviço de sincronização iniciado")
    except Exception as e:
        print(f"❌ Erro ao iniciar sincronização: {e}")
    
    # Executar primeira sincronização se necessário
    try:
        print("🔄 Verificando necessidade de sincronização inicial...")
        test_sql_computers = sql_manager.get_computers_from_sql()
        if len(test_sql_computers) == 0:
            print("🔄 Executando sincronização inicial...")
            sync_service.sync_ad_to_sql()
            print("✅ Sincronização inicial concluída")
        else:
            print(f"ℹ️  Sincronização inicial não necessária - {len(test_sql_computers)} computadores já em cache")
    except Exception as e:
        print(f"⚠️  Erro na sincronização inicial: {e}")
    

    
    # Configurar e iniciar servidor Flask
    app.run(
        debug=os.getenv('FLASK_ENV') == 'development',
        host='0.0.0.0',
        port=42057,
        threaded=True
    )
                        