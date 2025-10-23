from ldap3 import Server, Connection, ALL, SUBTREE
import logging
from ..config import AD_SERVER, AD_USERNAME, AD_PASSWORD, AD_BASE_DN

logger = logging.getLogger(__name__)


class ADManager:
    def __init__(self):
        self.server = Server(AD_SERVER, get_info=ALL)
        self.connection = None

    def connect(self):
        try:
            self.connection = Connection(self.server, user=AD_USERNAME, password=AD_PASSWORD, auto_bind=True)
            return True
        except Exception:
            logger.exception('AD connect failed')
            return False

    def get_computers(self):
        if not self.connect():
            return []

        try:
            search_filter = '(&(objectClass=computer)(!(primaryGroupID=516))( !(userAccountControl:1.2.840.113556.1.4.803:=8192) ))'
            attributes = ['cn', 'distinguishedName', 'lastLogonTimestamp', 'operatingSystem', 'operatingSystemVersion', 'whenCreated', 'description', 'userAccountControl', 'primaryGroupID', 'servicePrincipalName', 'dNSHostName']
            self.connection.search(search_base=AD_BASE_DN, search_filter=search_filter, search_scope=SUBTREE, attributes=attributes, paged_size=1000)

            computers = []
            for entry in self.connection.entries:
                try:
                    uac = int(entry.userAccountControl.value) if entry.userAccountControl.value else 0
                    is_disabled = bool(uac & 2)
                    last_logon = entry.lastLogonTimestamp.value.isoformat() if entry.lastLogonTimestamp.value else None

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
                except Exception:
                    logger.exception('Error processing AD entry')

            return computers
        except Exception:
            logger.exception('get_computers failed')
            return []
        finally:
            try:
                if self.connection:
                    self.connection.unbind()
            except Exception:
                pass


# Singleton instance for FastAPI
ad_manager = ADManager()
