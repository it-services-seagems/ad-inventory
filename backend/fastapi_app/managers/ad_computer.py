from ldap3 import Server, Connection, ALL, SUBTREE, MODIFY_REPLACE, MODIFY_DELETE
import logging
import subprocess
import re
from datetime import timezone
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
            self.connection.search(search_base=AD_BASE_DN, search_filter=search_filter, search_scope=SUBTREE, attributes=[
                'cn', 'distinguishedName', 'userAccountControl', 'description',
                'operatingSystem', 'lastLogonTimestamp', 'lastLogon'
            ])

            if not self.connection.entries:
                raise Exception(f"Computador '{computer_name}' não encontrado no Active Directory")

            computer = self.connection.entries[0]
            dn = str(computer.distinguishedName)
            uac = int(computer.userAccountControl.value) if computer.userAccountControl.value else 0
            is_disabled = bool(uac & 2)

            # Get the most recent logon timestamp (lastLogonTimestamp is replicated, lastLogon is per-DC)
            last_logon_ts = None
            try:
                ts1 = computer.lastLogonTimestamp.value if hasattr(computer, 'lastLogonTimestamp') and computer.lastLogonTimestamp.value else None
                ts2 = computer.lastLogon.value if hasattr(computer, 'lastLogon') and computer.lastLogon.value else None
                # Pick the most recent one
                if ts1 and ts2:
                    last_logon_ts = max(ts1, ts2)
                else:
                    last_logon_ts = ts1 or ts2
            except Exception:
                pass

            return {
                'name': str(computer.cn),
                'dn': dn,
                'userAccountControl': uac,
                'disabled': is_disabled,
                'description': str(computer.description) if computer.description else '',
                'operatingSystem': str(computer.operatingSystem) if computer.operatingSystem else '',
                'lastLogon': last_logon_ts.replace(tzinfo=timezone.utc).isoformat() if last_logon_ts and last_logon_ts.tzinfo is None else (last_logon_ts.isoformat() if last_logon_ts else None)
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
    def set_computer_description(self, computer_name, description):
        if description is None:
            raise ValueError('Descrição não fornecida')

        # Find the computer first (this will connect/disconnect)
        computer = self.find_computer(computer_name)

        # Reconnect to perform modify
        if not self.connect():
            raise Exception('Falha na conexão com Active Directory')

        def _sanitize(desc):
            s = str(desc)
            # Remove nulls and C0 control characters that commonly trigger invalidAttributeSyntax
            s = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", "", s)
            # Trim to AD description practical limit
            if len(s) > 1024:
                s = s[:1024]
            return s

        raw_desc = description
        sanitized = _sanitize(raw_desc)

        try:
            dn = computer.get('dn')

            # If sanitized is empty, attempt to delete the attribute instead of setting empty string
            if not sanitized or sanitized.strip() == '':
                success = self.connection.modify(dn, {'description': [(MODIFY_DELETE, [])]})
                if not success:
                    error_info = self.connection.result
                    err_text = error_info.get('description', '') if isinstance(error_info, dict) else str(error_info)
                    raise Exception(f"Falha na remoção da descrição no AD: {err_text}")

                return {
                    'success': True,
                    'message': f'Descrição do computador {computer_name} removida com sucesso',
                    'operation': {
                        'computer_name': computer_name,
                        'new_description': ''
                    }
                }

            success = self.connection.modify(dn, {'description': [(MODIFY_REPLACE, [sanitized])]})

            if not success:
                error_info = self.connection.result
                err_text = error_info.get('description', '') if isinstance(error_info, dict) else str(error_info)
                # Try a more aggressive sanitization if we detect attribute syntax problem
                if 'invalidAttributeSyntax' in err_text or 'invalid attribute syntax' in err_text.lower():
                    try:
                        # Remove any remaining non-printable characters
                        aggressive = ''.join(ch for ch in sanitized if ord(ch) >= 32 and ord(ch) != 127)
                        if len(aggressive) > 1024:
                            aggressive = aggressive[:1024]
                        success2 = self.connection.modify(dn, {'description': [(MODIFY_REPLACE, [aggressive])]})
                        if success2:
                            return {
                                'success': True,
                                'message': f'Descrição do computador {computer_name} atualizada com sucesso (sanitizada)',
                                'operation': {
                                    'computer_name': computer_name,
                                    'new_description': aggressive
                                }
                            }
                    except Exception:
                        logger.exception('aggressive sanitize attempt failed')

                raise Exception(f"Falha na modificação do AD: {err_text}")

            return {
                'success': True,
                'message': f'Descrição do computador {computer_name} atualizada com sucesso',
                'operation': {
                    'computer_name': computer_name,
                    'new_description': sanitized
                }
            }
        except Exception:
            logger.exception('set_computer_description failed')
            raise
        finally:
            self.disconnect()

    def set_computer_description_powershell(self, computer_name, description):
        try:
            # Escape double quotes in description for PowerShell command
            safe_desc = str(description).replace('"', '\\"')
            ps_command = f"Set-ADComputer -Identity '{computer_name}' -Description \"{safe_desc}\"; $c = Get-ADComputer -Identity '{computer_name}' -Properties description; Write-Output \"SUCCESS: $($c.Description)\""

            full_command = [
                'powershell.exe',
                '-ExecutionPolicy', 'Bypass',
                '-Command',
                f"try {{ Import-Module ActiveDirectory -ErrorAction Stop; {ps_command} }} catch {{ Write-Output \"ERROR: $($_.Exception.Message)\" }}"
            ]

            result = subprocess.run(full_command, capture_output=True, text=True, timeout=30)
            output = result.stdout.strip()
            error_output = result.stderr.strip()

            if result.returncode == 0 and output and output.startswith('SUCCESS:'):
                return {'success': True, 'message': f'Descrição atualizada com sucesso (PowerShell)', 'method': 'powershell', 'output': output}
            else:
                raise Exception(f"PowerShell falhou: {output or error_output}")
        except Exception:
            logger.exception('set_computer_description_powershell failed')
            raise


# Singleton
ad_computer_manager = ADComputerManager()
