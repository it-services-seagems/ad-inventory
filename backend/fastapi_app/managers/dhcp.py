from pypsrp.client import Client
import logging
import time
from datetime import datetime
from ..config import AD_USERNAME, AD_PASSWORD

logger = logging.getLogger(__name__)


class DHCPManager:
    """Simplified DHCP manager extracted from legacy app.py."""
    def __init__(self):
        self.org_to_servers = {
            "SHQ": ["ESMDC02"],
            "ESMERALDA": ["ESMDC02"],
            "DIAMANTE": ["DIADC02"],
            "TOPAZIO": ["TOPDC02"],
            "RUBI": ["RUBDC02"],
            "JADE": ["JADDC02"],
            "ONIX": ["ONIDC02"],
        }

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

        self.all_servers = [
            "DIADC02", "ESMDC02", "JADDC02", "RUBDC02", "ONIDC02", "TOPDC02",
        ]

        self.prefixos = ["SHQ", "ESM", "DIA", "TOP", "RUB", "JAD", "ONI", "CLO"]

        self.usuario = AD_USERNAME
        self.senha = AD_PASSWORD

    def get_organization_from_prefix(self, prefix):
        return self.prefix_to_org.get(prefix.upper(), prefix.upper())

    def testar_conexao_servidor(self, servidor):
        try:
            client = Client(
                server=servidor,
                username=self.usuario,
                password=self.senha,
                ssl=False,
                cert_validation=False,
                connection_timeout=10,
                operation_timeout=10,
            )

            script = "Write-Output 'OK'"
            output, streams, had_errors = client.execute_ps(script)
            if had_errors or 'OK' not in output:
                return None
            return client
        except Exception as e:
            logger.warning(f"Falha ao conectar em {servidor}: {str(e)[:100]}")
            return None

    def buscar_service_tag_servidor(self, servidor, service_tag):
        resultado = {'servidor': servidor, 'status': 'erro', 'macs': [], 'erro': None, 'tempo': 0}
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
                $matches = $filters | Where-Object {{$_.Description -like "*${{pattern}}*"}}
                if ($matches) {{ $found += $matches }}
            }}
            $unique = $found | Sort-Object MacAddress -Unique
            if ($unique) {{
                foreach ($filter in $unique) {{
                    Write-Output "MAC:$($filter.MacAddress)"
                    Write-Output "DESC:$($filter.Description)"
                    Write-Output "---"
                }}
            }} else {{ Write-Output "NENHUM_ENCONTRADO" }}
            """

            output, streams, had_errors = client.execute_ps(script)
            if had_errors:
                resultado['status'] = 'erro_dhcp'
                resultado['erro'] = '; '.join([str(error) for error in streams.error])
                return resultado

            if 'NENHUM_ENCONTRADO' in output:
                resultado['status'] = 'nao_encontrado'
            else:
                lines = output.strip().split('\n')
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
                        macs.append({'mac': current_mac, 'description': desc, 'pattern_found': pattern_encontrado, 'server': servidor, 'filter_type': 'Allow', 'mac_address': current_mac, 'match_field': 'description', 'name': ''})
                resultado['macs'] = macs
                resultado['status'] = 'encontrado' if macs else 'nao_encontrado'

        except Exception as e:
            resultado['status'] = 'erro'
            resultado['erro'] = str(e)
            logger.error(f"❌ Erro DHCP {servidor}: {str(e)[:100]}")
        finally:
            resultado['tempo'] = time.time() - inicio
        return resultado


# Singleton
dhcp_manager = DHCPManager()
