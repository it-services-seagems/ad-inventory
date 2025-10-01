import time
import json
import logging
from datetime import datetime, timedelta
from pypsrp.client import Client

logger = logging.getLogger(__name__)

class ADEventLogLastUserService:
    """
    Ported ADEventLogLastUserService from legacy Flask app.
    """
    def __init__(self, domain_controller=None, usuario=None, senha=None, ad_server=None, ad_base_dn=None):
        self.usuario = usuario
        self.senha = senha
        self.domain_controller = domain_controller
        self.connection_timeout = 15
        self.operation_timeout = 60
        self.max_events = 200

    def _resolve_domain_controller(self, ad_server, ad_base_dn):
        if ad_server:
            return ad_server.replace('ldap://', '').replace('ldaps://', '')
        if ad_base_dn:
            parts = [p.strip()[3:] for p in ad_base_dn.split(',') if p.strip().upper().startswith('DC=')]
            if parts:
                return '.'.join(parts)
        return None

    def conectar_domain_controller(self, dc_name):
        try:
            client = Client(
                server=dc_name,
                username=self.usuario,
                password=self.senha,
                ssl=False,
                cert_validation=False,
                connection_timeout=self.connection_timeout,
                operation_timeout=self.operation_timeout
            )
            # quick connectivity test
            test_script = "Write-Output 'CONNECTION_OK'"
            output, streams, had_errors = client.execute_ps(test_script)
            if had_errors or 'CONNECTION_OK' not in output:
                logger.error('DC connectivity failed: %s %s', dc_name, output)
                return None
            return client
        except Exception as e:
            logger.error('Error connecting to DC %s: %s', dc_name, e)
            return None

    def buscar_ultimo_logon_por_computador(self, computer_name, dias_historico=30, dc_name=None):
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
            if not dc_name:
                resultado['error'] = 'No domain controller specified'
                return resultado

            client = self.conectar_domain_controller(dc_name)
            if not client:
                resultado['error'] = f'Unable to connect to DC {dc_name}'
                return resultado

            # Prepare search names
            computer_names_to_search = [computer_name.upper(), computer_name.lower(), f"{computer_name.upper()}$", f"{computer_name.lower()}$"]
            data_inicio = (datetime.now() - timedelta(days=dias_historico)).strftime('%Y-%m-%d')

            script = f"""
            try {{
                $startDate = Get-Date "{data_inicio}"
                $maxEvents = {self.max_events}
                $events = Get-WinEvent -FilterHashtable @{{LogName='Security'; ID=@(4624,4768,4769); StartTime=$startDate}} -MaxEvents $maxEvents -ErrorAction Stop | Sort-Object TimeCreated -Descending
                $results = @()
                foreach ($event in $events) {{
                    $xml = [xml]$event.ToXml()
                    $eventData = $xml.Event.EventData.Data
                    $targetUserName = ($eventData | Where-Object {{$_.Name -eq 'TargetUserName'}}).InnerText
                    $workstationName = ($eventData | Where-Object {{$_.Name -eq 'WorkstationName'}}).InnerText
                    $logonType = ($eventData | Where-Object {{$_.Name -eq 'LogonType'}}).InnerText
                    $sourceNetworkAddress = ($eventData | Where-Object {{$_.Name -eq 'IpAddress'}}).InnerText
                    $results += @{{TimeCreated=$event.TimeCreated.ToString('yyyy-MM-ddTHH:mm:ss.fffZ'); UserName=$targetUserName; WorkstationName=$workstationName; LogonType=$logonType; SourceIP=$sourceNetworkAddress; EventId=$event.Id}}
                }}
                $results | ConvertTo-Json -Compress
            }} catch {{
                Write-Output "ERROR_EVENTLOG: $($_.Exception.Message)"
            }}
            """

            output, streams, had_errors = client.execute_ps(script)
            if had_errors:
                resultado['error'] = 'PowerShell execution error'
                return resultado

            # try parse json
            try:
                content = output.strip()
                events_data = json.loads(content) if content else []
                if isinstance(events_data, dict):
                    events_data = [events_data]

                # filter user events
                user_events = [e for e in events_data if e.get('UserName') and not str(e.get('UserName')).endswith('$')]
                if user_events:
                    user_events.sort(key=lambda x: x.get('TimeCreated', ''), reverse=True)
                    last = user_events[0]
                    resultado.update({
                        'success': True,
                        'last_user': last.get('UserName'),
                        'last_logon_time': last.get('TimeCreated'),
                        'logon_type': last.get('LogonType'),
                        'recent_logons': user_events[:5],
                        'events_found': len(events_data),
                        'computer_found': True
                    })
                else:
                    resultado['error'] = 'No user events found'
                    resultado['computer_found'] = False

            except Exception as e:
                resultado['error'] = f'Error parsing DC output: {e}'

        except Exception as e:
            resultado['error'] = str(e)
        finally:
            resultado['search_time'] = round(time.time() - inicio, 2)
            resultado['total_time'] = resultado['search_time']

        return resultado

    def buscar_logon_por_service_tag_via_ad(self, service_tag, dias_historico=30, ad_manager=None, dc_name=None):
        resultado = {'service_tag': service_tag, 'success': False, 'computer_found': False, 'computer_name': None, 'error': None}
        try:
            # find machine via ad_manager if provided
            computer_name = None
            if ad_manager:
                computer_name = ad_manager.find_computer_by_service_tag(service_tag)

            if not computer_name:
                resultado['error'] = 'Machine not found in AD'
                return resultado

            resultado['computer_found'] = True
            resultado['computer_name'] = computer_name
            # delegate to buscar_ultimo_logon_por_computador
            logon = self.buscar_ultimo_logon_por_computador(computer_name, dias_historico, dc_name=dc_name)
            if logon.get('success'):
                resultado.update({
                    'success': True,
                    'last_user': logon.get('last_user'),
                    'last_logon_time': logon.get('last_logon_time'),
                    'recent_logons': logon.get('recent_logons'),
                    'events_found': logon.get('events_found')
                })
            else:
                resultado['error'] = logon.get('error')

        except Exception as e:
            resultado['error'] = str(e)

        return resultado
