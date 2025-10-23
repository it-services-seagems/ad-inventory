from ldap3 import Server, Connection, ALL, SUBTREE, MODIFY_REPLACE
import logging
import subprocess
from ..config import AD_SERVER, AD_USERNAME, AD_PASSWORD, AD_BASE_DN

logger = logging.getLogger(__name__)


class ADComputerManager:
    def __init__(self):
        self.server = Server(AD_SERVER, get_info=ALL)
        self.connection = None

    def connect(self):
        try:
            self.connection = Connection(self.server, user=AD_USERNAME, password=AD_PASSWORD, auto_bind=True)
            logger.info('Connected to AD')
            return True
        except Exception:
            logger.exception('AD connect failed')
            return False

    def disconnect(self):
        if self.connection:
            try:
                self.connection.unbind()
            except Exception:
                pass
            self.connection = None

    def find_computer(self, computer_name):
        if not self.connect():
            raise Exception('Falha na conexão com Active Directory')

        try:
            search_filter = f"(&(objectClass=computer)(|(cn={computer_name})(sAMAccountName={computer_name}$)))"
            self.connection.search(search_base=AD_BASE_DN, search_filter=search_filter, search_scope=SUBTREE, attributes=['cn', 'distinguishedName', 'userAccountControl', 'description', 'operatingSystem'])

            if not self.connection.entries:
                raise Exception(f"Computador '{computer_name}' não encontrado no Active Directory")

            computer = self.connection.entries[0]
            dn = str(computer.distinguishedName)
            uac = int(computer.userAccountControl.value) if computer.userAccountControl.value else 0
            is_disabled = bool(uac & 2)

            return {
                'name': str(computer.cn),
                'dn': dn,
                'userAccountControl': uac,
                'disabled': is_disabled,
                'description': str(computer.description) if computer.description else '',
                'operatingSystem': str(computer.operatingSystem) if computer.operatingSystem else ''
            }
        except Exception:
            logger.exception('find_computer failed')
            raise
        finally:
            self.disconnect()

    def toggle_computer_status(self, computer_name, action):
        if action not in ['enable', 'disable']:
            raise ValueError("Ação deve ser 'enable' ou 'disable'")

        if not self.connect():
            raise Exception('Falha na conexão com Active Directory')

        try:
            computer = self.find_computer(computer_name)
            current_uac = computer['userAccountControl']
            is_currently_disabled = computer['disabled']

            if action == 'disable' and is_currently_disabled:
                return {'success': True, 'message': f'Computador {computer_name} já está desativado', 'already_in_desired_state': True, 'current_status': {'disabled': is_currently_disabled, 'userAccountControl': current_uac}}

            if action == 'enable' and not is_currently_disabled:
                return {'success': True, 'message': f'Computador {computer_name} já está ativado', 'already_in_desired_state': True, 'current_status': {'disabled': is_currently_disabled, 'userAccountControl': current_uac}}

            if action == 'disable':
                new_uac = current_uac | 2
            else:
                new_uac = current_uac & ~2

            # Modify attribute
            if not self.connect():
                raise Exception('Falha na reconexão com Active Directory')

            success = self.connection.modify(computer['dn'], {'userAccountControl': [(MODIFY_REPLACE, [str(new_uac)])]})

            if not success:
                error_info = self.connection.result
                raise Exception(f"Falha na modificação do AD: {error_info.get('description', 'Erro desconhecido')}")

            action_text = 'desativado' if action == 'disable' else 'ativado'
            return {
                'success': True,
                'message': f'Computador {computer_name} {action_text} com sucesso',
                'operation': {
                    'computer_name': computer_name,
                    'action': action,
                    'previous_status': {'disabled': is_currently_disabled, 'userAccountControl': current_uac},
                    'new_status': {'disabled': action == 'disable', 'userAccountControl': new_uac}
                }
            }
        except Exception:
            logger.exception('toggle_computer_status failed')
            raise
        finally:
            self.disconnect()

    def toggle_computer_status_powershell(self, computer_name, action):
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
                f"try {{ Import-Module ActiveDirectory -ErrorAction Stop; {ps_command}; $computer = Get-ADComputer -Identity '{computer_name}' -Properties Enabled, userAccountControl; Write-Output \"SUCCESS: Computador {action_text}. Enabled: $($computer.Enabled), UAC: $($computer.userAccountControl)\" }} catch {{ Write-Output \"ERROR: $($_.Exception.Message)\" }}"
            ]

            result = subprocess.run(full_command, capture_output=True, text=True, timeout=30)
            output = result.stdout.strip()
            error_output = result.stderr.strip()

            if result.returncode == 0 and "SUCCESS:" in output:
                return {'success': True, 'message': f'Computador {computer_name} {action_text} com sucesso (PowerShell)', 'method': 'powershell', 'output': output}
            else:
                raise Exception(f"PowerShell falhou: {output or error_output}")
        except Exception:
            logger.exception('toggle_computer_status_powershell failed')
            raise


# Singleton
ad_computer_manager = ADComputerManager()
