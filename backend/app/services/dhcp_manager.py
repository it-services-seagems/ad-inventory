import time
import logging
import os
from datetime import datetime
from pypsrp.client import Client

logger = logging.getLogger(__name__)


class DHCPManager:
    """Gerenciador para busca de MACs por service tag nos servidores DHCP"""

    def __init__(self, usuario: str | None = None, senha: str | None = None):
        # Avoid importing app settings at module import time because pydantic
        # may validate required env vars before dotenv is loaded. Use os.getenv
        # fallback to keep module import-safe. If callers pass settings, they
        # can override usuario/senha via params.

        # Mapeamento CORRETO de organizações para servidores DHCP
        self.org_to_servers = {
            "SHQ": ["ESMDC02"],
            "ESMERALDA": ["ESMDC02"],
            "DIAMANTE": ["DIADC02"],
            "TOPAZIO": ["TOPDC02"],
            "RUBI": ["RUBDC02"],
            "JADE": ["JADDC02"],
            "ONIX": ["ONIDC02"],
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
            "CLO": "SHQ",
        }

        # Servidores a partir das configurações (quando mapeamento IPs/nomes estiver presente)
        # keep hostnames as in the legacy implementation
        self.all_servers = [s for s in ["DIADC02", "ESMDC02", "JADDC02", "RUBDC02", "ONIDC02", "TOPDC02"]]
        self.prefixos = ["SHQ", "ESM", "DIA", "TOP", "RUB", "JAD", "ONI", "CLO"]

        # Credenciais AD (use provided args or environment variables)
        self.usuario = usuario or os.getenv('AD_USERNAME')
        self.senha = senha or os.getenv('AD_PASSWORD')

        # Timeouts
        self.connection_timeout = 10
        self.operation_timeout = 10

    def get_organization_from_prefix(self, prefix: str) -> str:
        return self.prefix_to_org.get(prefix.upper(), prefix.upper())

    def testar_conexao_servidor(self, servidor: str):
        try:
            client = Client(
                server=servidor,
                username=self.usuario,
                password=self.senha,
                ssl=False,
                cert_validation=False,
                connection_timeout=self.connection_timeout,
                operation_timeout=self.operation_timeout,
            )

            script = "Write-Output 'OK'"
            output, streams, had_errors = client.execute_ps(script)
            if had_errors or 'OK' not in output:
                return None
            return client
        except Exception as e:
            logger.warning(f"Falha ao conectar em {servidor}: {str(e)[:200]}")
            return None

    def buscar_service_tag_servidor(self, servidor: str, service_tag: str) -> dict:
        resultado = {
            'servidor': servidor,
            'status': 'erro',
            'macs': [],
            'erro': None,
            'tempo': 0
        }

        inicio = time.time()
        try:
            client = self.testar_conexao_servidor(servidor)
            if not client:
                resultado['status'] = 'conexao_falhou'
                resultado['erro'] = 'Não foi possível conectar'
                return resultado

            patterns = [service_tag]
            for prefixo in self.prefixos:
                patterns.extend([
                    f"{prefixo}-{service_tag}",
                    f"{prefixo}_{service_tag}",
                    f"{prefixo} {service_tag}",
                    f"{prefixo}{service_tag}",
                ])

            patterns_str = "', '".join(patterns)
            script = f"""
            $patterns = @('{patterns_str}')
            $filters = Get-DhcpServerv4Filter -List Allow
            $found = @()

            foreach ($pattern in $patterns) {{
                $matches = $filters | Where-Object {{ $_.Description -like "*${{pattern}}*" }}
                if ($matches) {{ $found += $matches }}
            }}

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

            output, streams, had_errors = client.execute_ps(script)
            if had_errors:
                resultado['status'] = 'erro_dhcp'
                resultado['erro'] = '; '.join([str(error) for error in streams.error]) if streams else 'erro'
                return resultado

            if 'NENHUM_ENCONTRADO' in (output or ''):
                resultado['status'] = 'nao_encontrado'
            else:
                lines = (output or '').strip().split('\n')
                macs = []
                current_mac = None
                for line in lines:
                    line = line.strip()
                    if line.startswith('MAC:'):
                        current_mac = line.replace('MAC:', '').strip()
                    elif line.startswith('DESC:') and current_mac:
                        desc = line.replace('DESC:', '').strip()
                        pattern_encontrado = 'sem_prefixo'
                        for pattern in patterns:
                            if pattern.upper() in desc.upper():
                                pattern_encontrado = pattern
                                break

                        macs.append({
                            'mac': current_mac,
                            'description': desc,
                            'pattern_found': pattern_encontrado,
                            'server': servidor,
                            'filter_type': 'Allow',
                            'mac_address': current_mac,
                            'match_field': 'description',
                            'name': ''
                        })

                resultado['macs'] = macs
                resultado['status'] = 'encontrado' if macs else 'nao_encontrado'

        except Exception as e:
            resultado['status'] = 'erro'
            resultado['erro'] = str(e)
            logger.error(f"Erro DHCP {servidor}: {str(e)[:200]}")
        finally:
            resultado['tempo'] = time.time() - inicio

        return resultado

    def search_filters_by_organization(self, organization: str, service_tag: str, include_filters: bool = False) -> dict:
        organization_upper = (organization or '').upper().strip()
        if organization_upper in self.prefix_to_org:
            ship_name = self.prefix_to_org[organization_upper]
        else:
            ship_name = organization_upper

        original_service_tag = (service_tag or '').strip().upper()
        if not original_service_tag:
            raise ValueError('service_tag is required')

        clean_service_tag = original_service_tag
        for prefix in self.prefixos:
            if clean_service_tag.startswith(prefix):
                clean_service_tag = clean_service_tag[len(prefix):]
                break

        servidores_alvo = self.org_to_servers.get(ship_name, self.all_servers)

        macs_encontrados = []
        for servidor in servidores_alvo:
            try:
                resultado = self.buscar_service_tag_servidor(servidor, clean_service_tag)
                if resultado.get('status') == 'encontrado':
                    for mac_info in resultado.get('macs', []):
                        macs_encontrados.append(mac_info)
            except Exception:
                logger.exception('Erro ao consultar servidor %s', servidor)

        # Remover duplicatas por MAC
        macs_unicos = {}
        for mac_info in macs_encontrados:
            mac = mac_info.get('mac')
            if mac and mac not in macs_unicos:
                macs_unicos[mac] = mac_info

        macs_finais = list(macs_unicos.values())

        if macs_finais:
            response_data = {
                'ship_name': ship_name,
                'dhcp_server': servidores_alvo[0] if servidores_alvo else 'N/A',
                'service_tag': original_service_tag,
                'service_tag_found': True,
                'search_results': macs_finais,
                'filters': {
                    'total': len(macs_finais),
                    'allow_count': len([m for m in macs_finais if m.get('filter_type') == 'Allow']),
                    'deny_count': len([m for m in macs_finais if m.get('filter_type') == 'Deny'])
                },
                'timestamp': datetime.now().isoformat(),
                'source': 'dhcp_filters'
            }
        else:
            response_data = {
                'ship_name': ship_name,
                'dhcp_server': servidores_alvo[0] if servidores_alvo else 'N/A',
                'service_tag': original_service_tag,
                'service_tag_found': False,
                'search_results': [],
                'error': 'Máquina não encontrada nos filtros DHCP',
                'filters': {'total': 0, 'allow_count': 0, 'deny_count': 0},
                'timestamp': datetime.now().isoformat(),
                'source': 'dhcp_filters_not_found'
            }

        return response_data

    def search_post(self, service_tag: str, ships: list | None = None) -> dict:
        service_tag = (service_tag or '').strip()
        if not service_tag:
            return {'success': False, 'message': 'Campo "service_tag" é obrigatório no body'}

        if ships and len(ships) > 0:
            servidores_alvo = []
            for ship in ships:
                ship_name = self.get_organization_from_prefix(ship)
                ship_servers = self.org_to_servers.get(ship_name, [])
                servidores_alvo.extend(ship_servers)
            servidores_alvo = list(set(servidores_alvo))
        else:
            servidores_alvo = self.all_servers

        clean_service_tag = service_tag.upper()
        for prefix in self.prefixos:
            if clean_service_tag.startswith(prefix):
                clean_service_tag = clean_service_tag[len(prefix):]
                break

        resultados_por_servidor = []
        macs_encontrados = []
        for servidor in servidores_alvo:
            try:
                resultado = self.buscar_service_tag_servidor(servidor, clean_service_tag)
                if resultado.get('status') == 'encontrado':
                    for mac_info in resultado.get('macs', []):
                        macs_encontrados.append(mac_info)

                    resultados_por_servidor.append({
                        'ship_name': 'UNKNOWN',
                        'dhcp_server': servidor,
                        'matches': resultado.get('macs', []),
                        'filters_summary': {
                            'total': len(resultado.get('macs', [])),
                            'allow_count': len([m for m in resultado.get('macs', []) if m.get('filter_type') == 'Allow']),
                            'deny_count': 0
                        }
                    })
            except Exception:
                logger.exception('Erro ao consultar servidor %s', servidor)

        macs_unicos = {}
        for mac_info in macs_encontrados:
            mac = mac_info.get('mac')
            if mac and mac not in macs_unicos:
                macs_unicos[mac] = mac_info

        macs_finais = list(macs_unicos.values())

        response_data = {
            'found': len(macs_finais) > 0,
            'service_tag': service_tag,
            'clean_service_tag': clean_service_tag,
            'results': resultados_por_servidor,
            'total_matches': len(macs_finais),
            'timestamp': datetime.now().isoformat()
        }

        return response_data

    def test_connections(self) -> dict:
        resultados = {}
        for servidor in self.all_servers:
            inicio = time.time()
            try:
                client = self.testar_conexao_servidor(servidor)
                tempo = time.time() - inicio
                if client:
                    resultados[servidor] = {'status': 'conectado', 'tempo': round(tempo, 2), 'erro': None}
                else:
                    resultados[servidor] = {'status': 'falhou', 'tempo': round(tempo, 2), 'erro': 'Falha na conexão'}
            except Exception as e:
                tempo = time.time() - inicio
                resultados[servidor] = {'status': 'erro', 'tempo': round(tempo, 2), 'erro': str(e)}

        total_servidores = len(resultados)
        servidores_ok = sum(1 for r in resultados.values() if r['status'] == 'conectado')
        servidores_erro = total_servidores - servidores_ok

        return {
            'success': True,
            'resumo': {
                'total_servidores': total_servidores,
                'servidores_ok': servidores_ok,
                'servidores_erro': servidores_erro,
                'percentual_sucesso': round((servidores_ok / total_servidores) * 100, 1) if total_servidores else 0
            },
            'detalhes': resultados,
            'timestamp': datetime.now().isoformat()
        }

    def get_servers_info(self) -> dict:
        return {
            'success': True,
            'servers': self.all_servers,
            'organization_mapping': self.org_to_servers,
            'prefix_mapping': self.prefix_to_org,
            'supported_prefixes': self.prefixos,
            'total_servers': len(self.all_servers),
            'dhcp_user': self.usuario,
            'timestamp': datetime.now().isoformat()
        }


# Instantiate a shared manager for router use
dhcp_manager = DHCPManager()
