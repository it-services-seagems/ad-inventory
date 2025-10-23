"""
PowerShell Manager for WinRM connections to domain controllers
Handles authentication and remote PowerShell execution for user detection
"""

import os
import logging
from typing import Optional, Dict, Any, Tuple
from pypsrp.client import Client
from pypsrp.exceptions import AuthenticationError, WinRMError
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class PowerShellManager:
    """Manages PowerShell connections to domain controllers for user operations"""
    
    def __init__(self):
        # Primary domain controller for PowerShell operations
        self.primary_dc = os.getenv('WINRM_SERVER', 'CLODC02')
        
        # Administrative credentials for WinRM
        self.admin_username = os.getenv('WINRM_USERNAME', 'SNM\\adm.automation')
        self.admin_password = os.getenv('WINRM_PASSWORD', '')
        
        # Connection settings
        self.connection_timeout = int(os.getenv('WINRM_CONNECTION_TIMEOUT', '15'))
        self.operation_timeout = int(os.getenv('WINRM_OPERATION_TIMEOUT', '30'))
        
        # Validate configuration
        if not self.admin_password:
            logger.warning("⚠️ WINRM_PASSWORD não configurada no .env")
        
        logger.info(f"🔧 PowerShell Manager configurado - Servidor: {self.primary_dc}, Usuário: {self.admin_username}")
    
    def create_client(self, server: str = None) -> Optional[Client]:
        """Create a WinRM client connection to the specified server"""
        target_server = server or self.primary_dc
        
        try:
            client = Client(
                server=target_server,
                username=self.admin_username,
                password=self.admin_password,
                ssl=False,  # Internal network, no SSL needed
                cert_validation=False,
                connection_timeout=self.connection_timeout,
                operation_timeout=self.operation_timeout,
                # Additional WinRM settings for better compatibility
                auth='ntlm',  # Explicitly use NTLM authentication
                encryption='auto'  # Let pypsrp choose the best encryption method
            )
            
            # Test the connection with a simple command
            test_script = "Write-Output 'CONNECTION_OK'"
            output, streams, had_errors = client.execute_ps(test_script)
            
            if had_errors or 'CONNECTION_OK' not in output:
                logger.error(f"❌ Teste de conexão falhou para {target_server}")
                return None
            
            logger.info(f"✅ Conexão WinRM estabelecida: {target_server}")
            return client
            
        except AuthenticationError as e:
            logger.error(f"❌ Erro de autenticação WinRM {target_server}: {e}")
            return None
        except WinRMError as e:
            logger.error(f"❌ Erro WinRM {target_server}: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Erro geral na conexão WinRM {target_server}: {e}")
            return None
    
    def execute_user_detection_script(self, computer_name: str, client: Client = None) -> Dict[str, Any]:
        """Execute PowerShell script to detect current user on a remote computer"""
        
        # Use provided client or create a new one
        if client is None:
            client = self.create_client()
            if not client:
                return {
                    'status': 'connection_failed',
                    'message': 'Could not establish WinRM connection to domain controller',
                    'computer_name': computer_name
                }
        
        # PowerShell script for user detection
        script = f"""
        try {{
            # First verify computer exists in AD and check if it's a server/DC
            $computer = Get-ADComputer -Identity "{computer_name}" -Properties OperatingSystem -ErrorAction Stop
            
            if ($computer.OperatingSystem -like "*Server*" -or $computer.Name -like "*DC*" -or $computer.Name -like "*SVR*") {{
                Write-Output "SKIP_SERVER_DC"
                exit 0
            }}
            
            # Try to get current logged user
            try {{
                $userInfo = Get-CimInstance Win32_ComputerSystem -ComputerName "{computer_name}" -ErrorAction Stop
                $currentUser = $userInfo.UserName
                
                if ($currentUser -and $currentUser.Trim() -ne "") {{
                    Write-Output "USER:$currentUser"
                }} else {{
                    Write-Output "USER:NONE"
                }}
            }} catch {{
                if ($_.Exception.Message -like "*RPC*" -or $_.Exception.Message -like "*network*" -or $_.Exception.Message -like "*timeout*" -or $_.Exception.Message -like "*access*") {{
                    Write-Output "STATUS:OFFLINE"
                    exit 0
                }} else {{
                    Write-Output "USER:NONE"
                }}
            }}
            
            # Try to get serial number for additional validation
            try {{
                $biosInfo = Get-CimInstance Win32_BIOS -ComputerName "{computer_name}" -ErrorAction Stop
                $serial = $biosInfo.SerialNumber
                if ($serial -and $serial.Trim() -ne "") {{
                    Write-Output "SERIAL:$serial"
                }}
            }} catch {{
                # Serial is optional, don't fail if we can't get it
            }}
            
            Write-Output "STATUS:OK"
            
        }} catch [Microsoft.ActiveDirectory.Management.ADIdentityNotFoundException] {{
            Write-Output "STATUS:NOT_FOUND"
            Write-Output "ERROR:Computer not found in Active Directory"
        }} catch {{
            Write-Output "STATUS:ERROR"
            Write-Output "ERROR:$($_.Exception.Message)"
        }}
        """
        
        try:
            # Execute the script
            output, streams, had_errors = client.execute_ps(script)
            
            # Parse the output
            result = self._parse_script_output(output, computer_name)
            
            # Add stream information for debugging if there were errors
            if had_errors and streams:
                error_info = []
                if hasattr(streams, 'error') and streams.error:
                    for error in streams.error:
                        error_info.append(str(error))
                if error_info:
                    result['ps_errors'] = error_info
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro ao executar script PowerShell para {computer_name}: {e}")
            return {
                'status': 'script_error',
                'message': f'Error executing PowerShell script: {str(e)}',
                'computer_name': computer_name
            }
    
    def _parse_script_output(self, output: str, computer_name: str) -> Dict[str, Any]:
        """Parse PowerShell script output and return structured result"""
        result = {
            'status': 'error',
            'computer_name': computer_name,
            'usuario_atual': None,
            'serial_number': None,
            'message': 'Unknown error'
        }
        
        if not output:
            result['message'] = 'No output from PowerShell script'
            return result
        
        lines = output.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            
            if line == 'SKIP_SERVER_DC':
                result['status'] = 'skipped'
                result['message'] = 'Machine is server or domain controller - skipped'
                return result
            
            elif line.startswith('USER:'):
                user = line.replace('USER:', '').strip()
                if user and user != 'NONE':
                    # Format user name: SNM\nome.sobrenome -> Nome Sobrenome
                    formatted_user = self._format_username(user)
                    result['usuario_atual'] = formatted_user
                    result['raw_user'] = user
                else:
                    result['usuario_atual'] = 'Nenhum usuário logado'
                    result['status'] = 'no_user'
            
            elif line.startswith('SERIAL:'):
                result['serial_number'] = line.replace('SERIAL:', '').strip()
            
            elif line.startswith('STATUS:'):
                status = line.replace('STATUS:', '').strip()
                if status == 'OK':
                    result['status'] = 'ok'
                elif status == 'OFFLINE':
                    result['status'] = 'unreachable'
                    result['message'] = 'Computer is offline or unreachable'
                elif status == 'NOT_FOUND':
                    result['status'] = 'not_found'
                    result['message'] = 'Computer not found in Active Directory'
                elif status == 'ERROR':
                    result['status'] = 'error'
            
            elif line.startswith('ERROR:'):
                result['message'] = line.replace('ERROR:', '').strip()
        
        # If we got a user but status is still error, mark as ok
        if result['status'] == 'error' and result['usuario_atual'] and result['usuario_atual'] != 'Nenhum usuário logado':
            result['status'] = 'ok'
        
        return result
    
    def _format_username(self, raw_username: str) -> str:
        """Format username from domain format to display format"""
        if not raw_username or raw_username == 'NONE':
            return 'Nenhum usuário logado'
        
        try:
            # Handle domain\username format
            if '\\' in raw_username:
                domain, username = raw_username.split('\\', 1)
                # Handle nome.sobrenome format
                if '.' in username:
                    first_name, last_name = username.split('.', 1)
                    return f"{first_name.title()} {last_name.title()}"
                else:
                    return username.title()
            else:
                # No domain, just format the username
                if '.' in raw_username:
                    first_name, last_name = raw_username.split('.', 1)
                    return f"{first_name.title()} {last_name.title()}"
                else:
                    return raw_username.title()
        
        except Exception as e:
            logger.warning(f"⚠️ Erro ao formatar usuário '{raw_username}': {e}")
            return raw_username
    
    def test_connection(self) -> Dict[str, Any]:
        """Test connection to the primary domain controller"""
        client = self.create_client()
        if client:
            return {
                'status': 'success',
                'server': self.primary_dc,
                'username': self.admin_username,
                'message': 'Connection successful'
            }
        else:
            return {
                'status': 'failed',
                'server': self.primary_dc,
                'username': self.admin_username,
                'message': 'Connection failed'
            }

# Global instance
powershell_manager = PowerShellManager()