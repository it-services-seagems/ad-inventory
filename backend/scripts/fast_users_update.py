#!/usr/bin/env python3

import os
import sys
import time
import pyodbc
import logging
import subprocess
import socket
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from pathlib import Path

backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

load_dotenv(dotenv_path=backend_dir / '.env')

try:
    from fastapi_app.config import SQL_SERVER, SQL_DATABASE, SQL_USERNAME, SQL_PASSWORD, USE_WINDOWS_AUTH
    try:
        from fastapi_app.config import settings as api_settings
    except Exception:
        api_settings = None
except ImportError:
    SQL_SERVER = os.getenv('SQL_SERVER', 'CLOSQL02')
    SQL_DATABASE = os.getenv('SQL_DATABASE', 'DellReports')
    SQL_USERNAME = os.getenv('SQL_USERNAME')
    SQL_PASSWORD = os.getenv('SQL_PASSWORD')
    USE_WINDOWS_AUTH = os.getenv('USE_WINDOWS_AUTH', 'true').lower() == 'true'

if 'api_settings' not in globals():
    api_settings = None

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fast_users_update.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FastUserUpdater:
    def __init__(self):
        self.connection_string = self._build_connection_string()
        self.error_codes = {
            'MACHINE_OFFLINE': 'Máquina offline - não responde ping',
            'PORT_135_BLOCKED': 'Porta RPC (135) bloqueada/fechada',
            'PORT_5985_BLOCKED': 'Porta WinRM HTTP (5985) bloqueada/fechada', 
            'PORT_5986_BLOCKED': 'Porta WinRM HTTPS (5986) bloqueada/fechada',
            'CONNECTION_FAILED': 'Falha na conexão geral com a máquina',
            'WINRM_DISABLED': 'WinRM desabilitado na máquina',
            'RPC_UNAVAILABLE': 'Serviço RPC não disponível',
            'ACCESS_DENIED': 'Acesso negado - credenciais inválidas',
            'TIMEOUT_EXPIRED': 'Tempo limite excedido para conexão',
            'POWERSHELL_ERROR': 'Erro na execução do PowerShell',
            'DB_UPDATE_FAILED': 'Falha ao atualizar banco de dados',
            'USER_NOT_FOUND': 'Nenhum usuário ativo detectado (console, RDP ou VPN)',
            'PSEXEC_FAILED': 'Falha na execução do PSExec',
            'NO_CREDENTIALS': 'Credenciais não configuradas',
            'DNS_RESOLUTION_FAILED': 'Falha na resolução DNS da máquina',
            'FIREWALL_BLOCKING': 'Firewall bloqueando conexões',
            'VPN_CONNECTIVITY_ISSUE': 'Possível problema de conectividade VPN',
            'RDP_DETECTION_FAILED': 'Falha na detecção de sessões RDP',
            'UNKNOWN_ERROR': 'Erro desconhecido'
        }
        
    def _build_connection_string(self):
        try:
            if USE_WINDOWS_AUTH:
                connection_string = f"""
                    DRIVER={{SQL Server}};
                    SERVER={SQL_SERVER};
                    DATABASE={SQL_DATABASE};
                    Trusted_Connection=yes;
                """
            else:
                connection_string = f"""
                    DRIVER={{SQL Server}};
                    SERVER={SQL_SERVER};
                    DATABASE={SQL_DATABASE};
                    UID={SQL_USERNAME};
                    PWD={SQL_PASSWORD};
                """
            
            logger.info(f"[CONFIG] Conectando ao SQL Server: {SQL_SERVER}/{SQL_DATABASE}")
            logger.info(f"[CONFIG] Usando Windows Auth: {USE_WINDOWS_AUTH}")
            return connection_string
            
        except Exception as e:
            logger.error(f"[CONFIG] Erro ao construir string de conexão: {e}")
            raise
    
    def check_machine_connectivity(self, computer_name, timeout=5):
        """Verifica conectividade básica da máquina"""
        connectivity_status = {
            'ping': False,
            'dns_resolution': False,
            'rpc_port': False,
            'winrm_http': False,
            'winrm_https': False
        }
        
        try:
            socket.gethostbyname(computer_name)
            connectivity_status['dns_resolution'] = True
        except socket.gaierror:
            return connectivity_status, 'DNS_RESOLUTION_FAILED'
        
        try:
            result = subprocess.run(['ping', '-n', '1', '-w', '3000', computer_name], 
                                  capture_output=True, text=True, timeout=timeout)
            if result.returncode == 0:
                connectivity_status['ping'] = True
        except:
            pass
        
        if not connectivity_status['ping']:
            return connectivity_status, 'MACHINE_OFFLINE'
        
        def check_port(port):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)  # Aumentado de 2s para 3s
                result = sock.connect_ex((computer_name, port))
                sock.close()
                return result == 0
            except:
                return False
        
        connectivity_status['rpc_port'] = check_port(135)
        connectivity_status['winrm_http'] = check_port(5985)
        connectivity_status['winrm_https'] = check_port(5986)
        
        if not connectivity_status['rpc_port']:
            return connectivity_status, 'PORT_135_BLOCKED'
        elif not connectivity_status['winrm_http'] and not connectivity_status['winrm_https']:
            return connectivity_status, 'PORT_5985_BLOCKED'
        
        return connectivity_status, None
    
    def get_all_shq_computers(self):
        query = """
        SELECT 
            id,
            name,
            Usuario_Atual
        FROM computers 
        WHERE name LIKE 'SHQ%' 
            AND is_enabled = 1
            AND is_domain_controller = 0
        ORDER BY name
        """
        
        try:
            with pyodbc.connect(self.connection_string) as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        'id': row.id,
                        'name': row.name,
                        'current_user': row.Usuario_Atual
                    })
                
                logger.info(f"[INFO] Encontradas {len(results)} maquinas SHQ para processar")
                return results
                
        except Exception as e:
            logger.error(f"[ERRO] Erro ao buscar maquinas: {e}")
            return []
    
    def get_user_fast(self, computer_name, timeout=10):
        try:
            ps_script = fr"""
            try {{
                $ErrorActionPreference = "Stop"
                
                # Método 1: Win32_ComputerSystem (usuário console)
                $consoleUser = $null
                try {{
                    $consoleUser = (Get-CimInstance Win32_ComputerSystem -ComputerName {computer_name} -OperationTimeoutSec 8).UserName
                }} catch {{ }}
                
                if ($consoleUser) {{
                    Write-Output "USER:$consoleUser"
                    Write-Output "METHOD:CONSOLE"
                    exit
                }}
                
                # Método 2: quser para sessões RDP
                $activeUser = $null
                try {{
                    $sessions = quser /server:{computer_name} 2>$null | Select-Object -Skip 1
                    if ($sessions) {{
                        foreach ($session in $sessions) {{
                            if ($session -match '^\s*(\S+)\s+' -and $session -match 'Active|Ativo') {{
                                $userName = $matches[1].Trim()
                                if ($userName -and $userName -ne 'USERNAME' -and $userName -notmatch 'services|console|SYSTEM') {{
                                    $activeUser = $userName
                                    break
                                }}
                            }}
                        }}
                    }}
                }} catch {{ }}
                
                if ($activeUser) {{
                    if ($activeUser -notmatch '\\') {{
                        Write-Output "USER:SNM\$activeUser"
                    }} else {{
                        Write-Output "USER:$activeUser"  
                    }}
                    Write-Output "METHOD:RDP_SESSION"
                    exit
                }}
                
                Write-Output "STATUS:NO_USER_LOGGED"
                Write-Output "METHOD:NO_ACTIVE_USER"
                
            }} catch [Microsoft.Management.Infrastructure.CimException] {{
                $error = $_.Exception.Message
                if ($error -match "Access.*denied" -or $error -match "permission") {{
                    Write-Output "ERROR:ACCESS_DENIED"
                }} elseif ($error -match "RPC" -or $error -match "endpoint") {{
                    Write-Output "ERROR:RPC_UNAVAILABLE" 
                }} elseif ($error -match "WinRM" -or $error -match "WSMan") {{
                    Write-Output "ERROR:WINRM_DISABLED"
                }} elseif ($error -match "timeout" -or $error -match "time.*out") {{
                    Write-Output "ERROR:CONNECTION_TIMEOUT"
                }} elseif ($error -match "network.*unreachable" -or $error -match "host.*not.*found") {{
                    Write-Output "ERROR:NETWORK_UNREACHABLE"
                }} else {{
                    Write-Output "ERROR:CIM_ERROR:$error"
                }}
            }} catch {{
                $error = $_.Exception.Message
                Write-Output "ERROR:GENERAL:$error"
            }}
            """
            
            result = subprocess.run([
                'powershell.exe', '-Command', ps_script
            ], capture_output=True, text=True, timeout=timeout)
            
            if result.returncode == 0:
                output_lines = result.stdout.strip().split('\n')
                user_line = None
                method_line = None
                
                for line in output_lines:
                    line = line.strip()
                    if line.startswith("USER:"):
                        user_line = line
                    elif line.startswith("METHOD:"):
                        method_line = line
                    elif line.startswith("STATUS:NO_USER_LOGGED"):
                        return (None, 'USER_NOT_FOUND')
                    elif line.startswith("ERROR:"):
                        error_type = line[6:]  # Remove "ERROR:" prefix
                        if "ACCESS_DENIED" in error_type:
                            return (None, 'ACCESS_DENIED')
                        elif "RPC_UNAVAILABLE" in error_type:
                            return (None, 'RPC_UNAVAILABLE') 
                        elif "WINRM_DISABLED" in error_type:
                            return (None, 'WINRM_DISABLED')
                        elif "CONNECTION_TIMEOUT" in error_type:
                            return (None, 'TIMEOUT_EXPIRED')
                        elif "NETWORK_UNREACHABLE" in error_type:
                            return (None, 'MACHINE_OFFLINE')
                        else:
                            return (None, 'POWERSHELL_ERROR')
                
                if user_line:
                    user = user_line[5:]  # Remove "USER:" prefix
                    detection_method = method_line[7:] if method_line else "UNKNOWN"
                    logger.debug(f"[{computer_name}] Usuário detectado via {detection_method}: {user}")
                    return (user, None)
            
            stderr_output = result.stderr.strip().lower()
            if 'access denied' in stderr_output or 'permission' in stderr_output:
                return (None, 'ACCESS_DENIED')
            elif 'rpc' in stderr_output:
                return (None, 'RPC_UNAVAILABLE')
            elif 'winrm' in stderr_output or 'wsman' in stderr_output:
                return (None, 'WINRM_DISABLED')
            else:
                return (None, 'CONNECTION_FAILED')
            
        except subprocess.TimeoutExpired:
            return (None, 'TIMEOUT_EXPIRED')
        except Exception as e:
            return (None, 'UNKNOWN_ERROR')

    def run_psexec_activate(self, computer_name, timeout=40):
        repo_default = str(Path(__file__).resolve().parents[3] / 'psexec' / 'PsExec.exe')
        hardcoded = r'C:\Automation\IT Inventory\ad-inventory\backend\psexec\PsExec.exe'
        psexec_env = hardcoded
        psexec_path = psexec_env or repo_default or hardcoded
        logger.info(f"[INFO] Usando PsExec em: {psexec_path}")

        username = os.getenv('AD_USERNAME', 'SNM\\adm.itservices')
        password = "xmZ7P@5vkKzg"

        if not os.path.exists(psexec_path):
            logger.error(f"[ERROR] PsExec nao encontrado em: {psexec_path}")
            return (False, 'PSEXEC_NOT_FOUND')
        target = f"\\\\{computer_name}"

        if USE_WINDOWS_AUTH and not password:
            logger.info(f"[INFO] USE_WINDOWS_AUTH ativo e sem AD_PASSWORD: tentando PsExec com usuario Windows atual para {computer_name}")
            args = [
                psexec_path,
                target,
                '-accepteula',
                '-s',
                'cmd.exe',
                '/c',
                'winrm quickconfig -q'
            ]
        else:
            if not password:
                logger.error(f"[ERROR] PSExec requerido, mas variavel AD_PASSWORD nao configurada para {computer_name}")
                return (False, 'NO_CREDENTIALS')

            args = [
                psexec_path,
                target,
                '-accepteula',
                '-h',
                '-u', username,
                '-p', password,
                '-s',
                'cmd.exe',
                '/c',
                'winrm quickconfig -q'
            ]

        try:
            logger.info(f"[INFO] Tentando PsExec->winrm quickconfig em {computer_name} com {username} (timeout={timeout}s)")
            proc = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
            output = (proc.stdout or '') + '\n' + (proc.stderr or '')
            rc = proc.returncode
            
            if rc == 0:
                logger.info(f"[INFO] PsExec executado (rc=0) em {computer_name}")
                return (True, output)
            else:
                if 'access denied' in output.lower():
                    return (False, 'ACCESS_DENIED')
                elif 'network path not found' in output.lower():
                    return (False, 'MACHINE_OFFLINE')
                else:
                    logger.warning(f"[WARN] PsExec rc={rc} em {computer_name}: {output}")
                    return (False, 'PSEXEC_FAILED')
                    
        except subprocess.TimeoutExpired:
            logger.warning(f"[WARN] PsExec timeout em {computer_name} (>{timeout}s)")
            return (False, 'TIMEOUT_EXPIRED')
        except Exception as e:
            logger.error(f"[ERROR] Erro ao executar PsExec em {computer_name}: {e}")
            return (False, 'UNKNOWN_ERROR')
    
    def format_username(self, domain_user):
        if not domain_user or '\\' not in domain_user:
            return domain_user
        
        try:
            username = domain_user.split('\\')[1]
            name_parts = username.replace('.', ' ').split()
            return ' '.join([part.capitalize() for part in name_parts])
        except:
            return domain_user
    
    def update_user_fast(self, computer_id, formatted_user):
        try:
            with pyodbc.connect(self.connection_string) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE computers SET Usuario_Atual = ?, updated_at = GETDATE() WHERE id = ?",
                    (formatted_user, computer_id)
                )
                conn.commit()
                return cursor.rowcount > 0
        except:
            return False
    
    def process_computer_fast(self, computer):
        computer_name = computer['name']
        computer_id = computer['id']
        
        start_time = time.time()
        failure_reason = None
        connectivity_details = {}
        
        # Primeiro teste direto, sem verificar conectividade previamente
        domain_user, error = self.get_user_fast(computer_name, timeout=10)

        if not domain_user and error:
            logger.debug(f"[{computer_name}] Primeiro teste falhou: {error}")
            
            # PSExec para casos que podem ser resolvidos (como versão original)
            should_attempt_psexec = error in ['WINRM_DISABLED', 'RPC_UNAVAILABLE', 'CONNECTION_FAILED', 'TIMEOUT_EXPIRED']
            failure_reason = error

            if should_attempt_psexec:
                logger.debug(f"[{computer_name}] Tentando PSExec...")
                ok, psexec_out = self.run_psexec_activate(computer_name, timeout=12)  
                if ok:
                    time.sleep(2)  
                    domain_user, error = self.get_user_fast(computer_name, timeout=12)  
                    if not domain_user:
                        failure_reason = f"PSEXEC_SUCCESS_BUT_{error}"
                else:
                    failure_reason = f"PSEXEC_FAILED_{psexec_out}"

        if domain_user:
            formatted_user = self.format_username(domain_user)
            success = self.update_user_fast(computer_id, formatted_user)

            elapsed = time.time() - start_time

            if success:
                return {
                    'computer': computer_name,
                    'success': True,
                    'user': formatted_user,
                    'time': elapsed,
                    'error_code': None,
                    'connectivity': connectivity_details
                }
            else:
                failure_reason = 'DB_UPDATE_FAILED'
        
        # Só faz verificação de conectividade no final, para diagnóstico
        if not domain_user and failure_reason:
            try:
                connectivity_status, connectivity_error = self.check_machine_connectivity(computer_name, timeout=2)
                connectivity_details = connectivity_status
                if connectivity_error == 'MACHINE_OFFLINE':
                    failure_reason = 'MACHINE_OFFLINE'
            except:
                pass  # Não falhar por causa de diagnóstico
        
        return {
            'computer': computer_name,
            'success': False,
            'time': time.time() - start_time,
            'error_code': failure_reason or 'UNKNOWN_ERROR',
            'error_description': self.error_codes.get(failure_reason or 'UNKNOWN_ERROR', 'Erro não identificado'),
            'connectivity': connectivity_details
        }
    
    def run_fast_update(self, max_workers=20):
        logger.info(f"[START] Iniciando processamento OTIMIZADO de todas as maquinas SHQ...")
        logger.info(f"[CONFIG] Workers: {max_workers}, Timeout otimizado para velocidade")
        
        start_time = time.time()
        
        computers = self.get_all_shq_computers()
        
        if not computers:
            logger.warning("[WARN] Nenhuma maquina SHQ encontrada")
            return
        
        results = []
        success_count = 0
        error_summary = {}
        connectivity_summary = {
            'total_offline': 0,
            'dns_failed': 0,
            'rpc_blocked': 0,
            'winrm_blocked': 0,
            'firewall_issues': 0
        }
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_computer = {
                executor.submit(self.process_computer_fast, computer): computer 
                for computer in computers
            }
            
            completed = 0
            for future in as_completed(future_to_computer):
                result = future.result()
                results.append(result)
                completed += 1
                
                if result['success']:
                    success_count += 1
                    logger.info(f"[{completed}/{len(computers)}] SUCCESS: {result['computer']} -> {result['user']} ({result['time']:.1f}s)")
                else:
                    error_code = result['error_code']
                    error_desc = result['error_description']
                    error_summary[error_code] = error_summary.get(error_code, 0) + 1
                    
                    connectivity = result.get('connectivity', {})
                    if error_code == 'MACHINE_OFFLINE':
                        connectivity_summary['total_offline'] += 1
                    elif error_code == 'DNS_RESOLUTION_FAILED':
                        connectivity_summary['dns_failed'] += 1
                    elif error_code == 'PORT_135_BLOCKED':
                        connectivity_summary['rpc_blocked'] += 1
                    elif error_code in ['PORT_5985_BLOCKED', 'PORT_5986_BLOCKED']:
                        connectivity_summary['winrm_blocked'] += 1
                    
                    conn_info = ""
                    if connectivity:
                        conn_status = []
                        if connectivity.get('ping'): conn_status.append("PING_OK")
                        if connectivity.get('dns_resolution'): conn_status.append("DNS_OK")
                        if connectivity.get('rpc_port'): conn_status.append("RPC_OK")
                        if connectivity.get('winrm_http'): conn_status.append("WINRM_HTTP_OK")
                        if connectivity.get('winrm_https'): conn_status.append("WINRM_HTTPS_OK")
                        if conn_status:
                            conn_info = f" [{','.join(conn_status)}]"
                    
                    logger.warning(f"[{completed}/{len(computers)}] FAIL: {result['computer']} ({result['time']:.1f}s) - {error_code}: {error_desc}{conn_info}")
                
                if completed % 10 == 0:
                    elapsed = time.time() - start_time
                    rate = completed / elapsed
                    remaining = len(computers) - completed
                    eta = remaining / rate if rate > 0 else 0
                    logger.info(f"[PROGRESS] {completed}/{len(computers)} concluidas ({success_count} sucessos) - ETA: {eta:.0f}s")
        
        total_time = time.time() - start_time
        
        logger.info("=" * 80)
        logger.info(f"[FINAL] RELATORIO COMPLETO")
        logger.info(f"Total de maquinas processadas: {len(computers)}")
        logger.info(f"Sucessos: {success_count}")
        logger.info(f"Falhas: {len(computers) - success_count}")
        logger.info(f"Taxa de sucesso: {(success_count/len(computers)*100):.1f}%")
        logger.info(f"Tempo total: {total_time:.1f}s")
        logger.info(f"Tempo medio por maquina: {total_time/len(computers):.1f}s")
        logger.info(f"Taxa de processamento: {len(computers)/total_time:.1f} maquinas/s")
        
        if error_summary:
            logger.info("RESUMO DE ERROS:")
            for error_code, count in sorted(error_summary.items(), key=lambda x: x[1], reverse=True):
                error_desc = self.error_codes.get(error_code, error_code)
                logger.info(f"  {error_code}: {count} ocorrencias - {error_desc}")
        
        logger.info("RESUMO DE CONECTIVIDADE:")
        logger.info(f"  Máquinas offline (não respondem ping): {connectivity_summary['total_offline']}")
        logger.info(f"  Falhas de resolução DNS: {connectivity_summary['dns_failed']}")
        logger.info(f"  Porta RPC (135) bloqueada: {connectivity_summary['rpc_blocked']}")
        logger.info(f"  Portas WinRM bloqueadas: {connectivity_summary['winrm_blocked']}")
        
        machines_with_connectivity_issues = (connectivity_summary['total_offline'] + 
                                           connectivity_summary['dns_failed'] + 
                                           connectivity_summary['rpc_blocked'] + 
                                           connectivity_summary['winrm_blocked'])
        
        if machines_with_connectivity_issues > 0:
            logger.info("RECOMENDAÇÕES:")
            if connectivity_summary['total_offline'] > 0:
                logger.info("  - Verificar máquinas offline: podem estar desligadas ou com problemas de rede")
            if connectivity_summary['rpc_blocked'] > 0:
                logger.info("  - Verificar firewall: porta RPC (135) pode estar bloqueada")
            if connectivity_summary['winrm_blocked'] > 0:
                logger.info("  - Verificar WinRM: portas 5985/5986 podem estar bloqueadas ou serviço desabilitado")
        
        logger.info("=" * 80)

    def test_single_machine(self, computer_name):
        """Testa uma única máquina com diagnóstico detalhado"""
        logger.info(f"[TEST] Iniciando teste detalhado para: {computer_name}")
        
        logger.info(f"[TEST] 1. Verificando conectividade básica...")
        connectivity_status, connectivity_error = self.check_machine_connectivity(computer_name)
        logger.info(f"[TEST] Conectividade: {connectivity_status}")
        if connectivity_error:
            logger.info(f"[TEST] Erro de conectividade: {connectivity_error}")
            return False
        
        logger.info(f"[TEST] 2. Testando detecção de usuário com múltiplos métodos...")
        
        # Teste com timeout aumentado para sessões RDP/VPN
        domain_user, error = self.get_user_fast(computer_name, timeout=20)
        
        if domain_user:
            logger.info(f"[TEST] ✅ Usuário detectado: {domain_user}")
            formatted_user = self.format_username(domain_user)
            logger.info(f"[TEST] ✅ Usuário formatado: {formatted_user}")
            
            # Teste de atualização no banco
            try:
                computers = self.get_all_shq_computers()
                target_computer = None
                for comp in computers:
                    if comp['name'].upper() == computer_name.upper():
                        target_computer = comp
                        break
                
                if target_computer:
                    success = self.update_user_fast(target_computer['id'], formatted_user)
                    if success:
                        logger.info(f"[TEST] ✅ Atualização no banco: SUCESSO")
                    else:
                        logger.info(f"[TEST] ❌ Atualização no banco: FALHOU")
                else:
                    logger.info(f"[TEST] ⚠️  Máquina não encontrada no banco")
            except Exception as e:
                logger.info(f"[TEST] ❌ Erro ao testar atualização no banco: {e}")
                
        else:
            logger.info(f"[TEST] ❌ Falha na detecção de usuário: {error}")
            
            if error == 'USER_NOT_FOUND':
                logger.info(f"[TEST] 📋 DIAGNÓSTICO para USER_NOT_FOUND:")
                logger.info(f"[TEST] - Isso pode indicar que:")
                logger.info(f"[TEST]   • Ninguém está logado na máquina")
                logger.info(f"[TEST]   • Usuário conectado via RDP mas não detectado")
                logger.info(f"[TEST]   • Problema na detecção de sessões ativas")
                logger.info(f"[TEST]   • Conectividade VPN interferindo na detecção")
                
                if connectivity_status.get('winrm_http') or connectivity_status.get('winrm_https'):
                    logger.info(f"[TEST] 3. WinRM disponível, tentando PSExec mesmo assim...")
                    ok, psexec_out = self.run_psexec_activate(computer_name, timeout=25)
                    if ok:
                        logger.info(f"[TEST] ✅ PSExec executado com sucesso")
                        time.sleep(4)
                        logger.info(f"[TEST] 4. Tentando detecção novamente após PSExec...")
                        domain_user, error = self.get_user_fast(computer_name, timeout=20)
                        if domain_user:
                            logger.info(f"[TEST] ✅ Usuário detectado após PSExec: {domain_user}")
                        else:
                            logger.info(f"[TEST] ❌ Ainda falhou após PSExec: {error}")
                    else:
                        logger.info(f"[TEST] ❌ PSExec falhou: {psexec_out}")
            
            elif error in ['WINRM_DISABLED', 'RPC_UNAVAILABLE', 'CONNECTION_FAILED', 'TIMEOUT_EXPIRED']:
                logger.info(f"[TEST] 3. Tentando PSExec para resolver {error}...")
                ok, psexec_out = self.run_psexec_activate(computer_name, timeout=25)
                if ok:
                    logger.info(f"[TEST] ✅ PSExec executado com sucesso")
                    time.sleep(4)
                    logger.info(f"[TEST] 4. Tentando detecção novamente...")
                    domain_user, error = self.get_user_fast(computer_name, timeout=20)
                    if domain_user:
                        logger.info(f"[TEST] ✅ Usuário detectado após PSExec: {domain_user}")
                    else:
                        logger.info(f"[TEST] ❌ Ainda falhou após PSExec: {error}")
                else:
                    logger.info(f"[TEST] ❌ PSExec falhou: {psexec_out}")
        
        logger.info(f"[TEST] 📊 RESUMO:")
        logger.info(f"[TEST] - Conectividade: {'✅ OK' if not connectivity_error else '❌ ' + connectivity_error}")
        logger.info(f"[TEST] - Detecção de usuário: {'✅ OK' if domain_user else '❌ ' + (error or 'UNKNOWN')}")
        logger.info(f"[TEST] - Resultado: {'✅ SUCESSO' if domain_user else '❌ FALHOU'}")
        
        if domain_user is None and error == 'USER_NOT_FOUND':
            logger.info(f"[TEST] 💡 DICAS PARA RESOLVER:")
            logger.info(f"[TEST] - Verifique se há realmente alguém logado na máquina")
            logger.info(f"[TEST] - Se está usando RDP, tente fazer logoff e login novamente")
            logger.info(f"[TEST] - Para VPN: pode ser necessário melhorar a conectividade")
            logger.info(f"[TEST] - Considere aumentar timeouts para conexões VPN")
        
        logger.info(f"[TEST] Teste concluído para {computer_name}")
        return domain_user is not None

def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == "--test" and len(sys.argv) > 2:
            computer_name = sys.argv[2]
            try:
                updater = FastUserUpdater()
                success = updater.test_single_machine(computer_name)
                if success:
                    logger.info(f"[SUCCESS] Teste da máquina {computer_name} foi bem-sucedido")
                else:
                    logger.error(f"[FAILED] Teste da máquina {computer_name} falhou")
            except KeyboardInterrupt:
                logger.info("[STOP] Teste interrompido pelo usuario")
            except Exception as e:
                logger.error(f"[CRITICAL] Erro critico no teste: {e}")
            return
        elif sys.argv[1] == "--help":
            print("Uso:")
            print("  python fast_users_update.py                    # Processar todas as máquinas")
            print("  python fast_users_update.py --test MACHINE     # Testar uma máquina específica")
            print("  python fast_users_update.py --help             # Mostrar esta ajuda")
            return
    
    try:
        updater = FastUserUpdater()
        updater.run_fast_update(max_workers=20)  # Reduzido para ser menos agressivo
        
    except KeyboardInterrupt:
        logger.info("[STOP] Processo interrompido pelo usuario")
    except Exception as e:
        logger.error(f"[CRITICAL] Erro critico: {e}")

if __name__ == "__main__":
    main()