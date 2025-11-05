import subprocess
import csv
import json
from datetime import datetime
import sys
import os
import logging

# Import connection managers
try:
    from fastapi_app.connections import require_ad_computer_manager
    from fastapi_app import managers as local_managers
    USE_AD_MANAGER = True
except ImportError:
    try:
        # Try relative import if running from backend directory
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from fastapi_app.connections import require_ad_computer_manager
        from fastapi_app import managers as local_managers
        USE_AD_MANAGER = True
    except ImportError:
        USE_AD_MANAGER = False
        print("⚠️ AD Manager não disponível, usando PowerShell direto")

logger = logging.getLogger(__name__)

def get_ad_computers_via_manager(limit=None):
    """
    Obtém lista de computadores do Active Directory usando AD Manager
    """
    try:
        ad_computer_manager = require_ad_computer_manager()
        
        # Use the existing find methods from AD computer manager
        if hasattr(ad_computer_manager, 'get_all_computers'):
            computers = ad_computer_manager.get_all_computers()
        elif hasattr(ad_computer_manager, 'find_all_computers'):
            computers = ad_computer_manager.find_all_computers()
        else:
            # Fallback to a basic search
            computers = []
            logger.warning("AD Computer Manager não tem método para buscar todos os computadores")
        
        # Extract computer names
        computer_names = []
        for comp in computers:
            if isinstance(comp, dict):
                name = comp.get('name') or comp.get('Name') or comp.get('cn')
            else:
                name = getattr(comp, 'name', None) or getattr(comp, 'cn', None)
            
            if name:
                computer_names.append(name)
        
        # Apply limit if specified
        if limit and len(computer_names) > limit:
            computer_names = computer_names[:limit]
        
        return computer_names
        
    except Exception as e:
        logger.error(f"Erro ao obter computadores via AD Manager: {e}")
        return []

def get_ad_computers_via_powershell(limit=None):
    """
    Obtém lista de computadores do Active Directory via PowerShell (fallback)
    """
    try:
        # PowerShell command to get AD computers with better error handling
        if limit:
            ps_command = f"""
            try {{
                Import-Module ActiveDirectory -ErrorAction Stop
                $computers = Get-ADComputer -Filter {{Enabled -eq $true}} -Properties Name -ErrorAction Stop | 
                             Select-Object Name -First {limit}
                if ($computers) {{
                    $computers | ConvertTo-Json -Compress
                }} else {{
                    Write-Output "[]"
                }}
            }} catch {{
                Write-Error $_.Exception.Message
                Write-Output "[]"
            }}
            """
        else:
            ps_command = """
            try {
                Import-Module ActiveDirectory -ErrorAction Stop
                $computers = Get-ADComputer -Filter {Enabled -eq $true} -Properties Name -ErrorAction Stop | 
                             Select-Object Name
                if ($computers) {
                    $computers | ConvertTo-Json -Compress
                } else {
                    Write-Output "[]"
                }
            } catch {
                Write-Error $_.Exception.Message
                Write-Output "[]"
            }
            """
        
        result = subprocess.run(
            ["powershell", "-Command", ps_command],
            capture_output=True,
            text=True,
            shell=True,
            timeout=60
        )
        
        if result.returncode == 0 and result.stdout.strip():
            try:
                computers_data = json.loads(result.stdout.strip())
                if not computers_data:
                    return []
                if isinstance(computers_data, dict):
                    return [computers_data['Name']]
                return [comp['Name'] for comp in computers_data if comp.get('Name')]
            except json.JSONDecodeError as e:
                print(f"Erro ao decodificar JSON: {e}")
                print(f"Saída do PowerShell: {result.stdout[:200]}...")
                return []
        else:
            error_msg = result.stderr or "Comando PowerShell falhou"
            print(f"Erro ao obter computadores do AD: {error_msg}")
            return []
            
    except subprocess.TimeoutExpired:
        print("Timeout ao executar comando PowerShell para obter computadores")
        return []
    except Exception as e:
        print(f"Erro ao conectar no AD: {e}")
        return []

def get_ad_computers(limit=None):
    """
    Obtém lista de computadores do Active Directory
    """
    if USE_AD_MANAGER:
        computers = get_ad_computers_via_manager(limit)
        if computers:
            return computers
        else:
            print("⚠️ Falha ao usar AD Manager, tentando PowerShell...")
    
    # Fallback to PowerShell
    return get_ad_computers_via_powershell(limit)

def get_computer_info(machine_name):
    """
    Executa o script PowerShell para obter informações da máquina
    """
    ps_script = f"""
    param (
        [Parameter(Mandatory = $true)]
        [string]$MachineName
    )

    try {{
        # Pega o usuário logado
        $user = (Get-CimInstance Win32_ComputerSystem -ComputerName $MachineName -ErrorAction Stop).UserName
        # Pega o serial da máquina
        $serial = (Get-CimInstance Win32_BIOS -ComputerName $MachineName -ErrorAction Stop).SerialNumber

        [PSCustomObject]@{{
            ComputerName = $MachineName
            SerialNumber = $serial
            LoggedUser   = if ($user) {{ $user }} else {{ "Nenhum usuário logado" }}
        }} | ConvertTo-Json

    }} catch {{
        [PSCustomObject]@{{
            ComputerName = $MachineName
            SerialNumber = "Erro ao conectar"
            LoggedUser   = "Erro ao conectar"
        }} | ConvertTo-Json
    }}
    """
    
    try:
        result = subprocess.run(
            ["powershell", "-Command", ps_script, "-MachineName", machine_name],
            capture_output=True,
            text=True,
            shell=True,
            timeout=30
        )
        
        if result.stdout.strip():
            return json.loads(result.stdout)
        else:
            return {
                "ComputerName": machine_name,
                "SerialNumber": "Timeout/Erro",
                "LoggedUser": "Timeout/Erro"
            }
            
    except subprocess.TimeoutExpired:
        return {
            "ComputerName": machine_name,
            "SerialNumber": "Timeout",
            "LoggedUser": "Timeout"
        }
    except Exception as e:
        return {
            "ComputerName": machine_name,
            "SerialNumber": f"Erro: {e}",
            "LoggedUser": f"Erro: {e}"
        }

def test_connections():
    """
    Testa as conexões disponíveis antes de executar
    """
    print("🔍 Testando conexões disponíveis...")
    
    if USE_AD_MANAGER:
        try:
            ad_computer_manager = require_ad_computer_manager()
            print("✅ AD Computer Manager disponível")
            return True
        except Exception as e:
            print(f"❌ AD Computer Manager não disponível: {e}")
            print("📋 Usando PowerShell como fallback")
            return False
    else:
        print("📋 Usando PowerShell para conexão AD")
        
        # Test PowerShell AD module
        try:
            test_result = subprocess.run(
                ["powershell", "-Command", "Import-Module ActiveDirectory; Get-Command Get-ADComputer"],
                capture_output=True,
                text=True,
                shell=True,
                timeout=10
            )
            if test_result.returncode == 0:
                print("✅ PowerShell AD Module disponível")
                return True
            else:
                print("❌ PowerShell AD Module não disponível")
                return False
        except Exception as e:
            print(f"❌ Erro ao testar PowerShell: {e}")
            return False

def main():
    print("🚀 Iniciando coleta de inventário de computadores\n")
    
    # Testa conexões
    test_connections()
    print()
    
    # Solicita quantas máquinas processar
    try:
        limit = input("Quantas máquinas você quer processar? (Enter para todas): ").strip()
        limit = int(limit) if limit else None
    except ValueError:
        limit = None
    
    print("Obtendo lista de computadores do Active Directory...")
    computers = get_ad_computers(limit)
    
    if not computers:
        print("Nenhum computador encontrado no AD.")
        return
    
    print(f"Encontrados {len(computers)} computadores. Iniciando coleta...")
    
    # Prepara arquivo CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"computer_inventory_{timestamp}.csv"
    csv_path = os.path.join(os.path.dirname(__file__), csv_filename)
    
    results = []
    
    # Processa cada computador
    for i, computer in enumerate(computers, 1):
        print(f"Processando {i}/{len(computers)}: {computer}")
        
        info = get_computer_info(computer)
        results.append(info)
        
        # Mostra progresso
        if i % 10 == 0:
            print(f"Progresso: {i}/{len(computers)} computadores processados")
    
    # Salva no CSV
    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['ComputerName', 'SerialNumber', 'LoggedUser']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for result in results:
            writer.writerow(result)
    
    print(f"\n✅ Processamento concluído!")
    print(f"📁 Arquivo salvo em: {csv_path}")
    print(f"📊 Total de computadores processados: {len(results)}")
    
    # Mostra estatísticas
    successful = len([r for r in results if "Erro" not in r['SerialNumber'] and "Timeout" not in r['SerialNumber']])
    print(f"✅ Sucessos: {successful}")
    print(f"❌ Falhas: {len(results) - successful}")

if __name__ == "__main__":
    main()
