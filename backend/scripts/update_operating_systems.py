#!/usr/bin/env python3
"""
Script para atualizar associações de sistema operacional nos computadores
"""

import pyodbc
import sys
import re

def normalize_os_name(os_name):
    """Normaliza nome do sistema operacional para busca"""
    if not os_name:
        return None
    
    os_name = os_name.strip()
    
    # Mapeamentos mais específicos primeiro
    mappings = {
        # Windows 10
        'Windows 10 Enterprise': 'Windows 10 Enterprise',
        'Windows 10 Pro': 'Windows 10 Pro', 
        'Windows 10 Professional': 'Windows 10 Pro',
        'Windows 10 Home': 'Windows 10 Home',
        
        # Windows 11
        'Windows 11 Enterprise': 'Windows 11 Enterprise',
        'Windows 11 Pro': 'Windows 11 Pro',
        'Windows 11 Professional': 'Windows 11 Pro',
        'Windows 11 Home': 'Windows 11 Home',
        
        # Windows Server
        'Windows Server 2019 Standard': 'Windows Server 2019 Standard',
        'Windows Server 2019 Datacenter': 'Windows Server 2019 Datacenter',
        'Windows Server 2022 Standard': 'Windows Server 2022 Standard', 
        'Windows Server 2022 Datacenter': 'Windows Server 2022 Datacenter',
        'Windows Server 2016 Standard': 'Windows Server 2016 Standard',
        'Windows Server 2012 R2 Standard': 'Windows Server 2012 R2 Standard',
        'Windows Server 2012 R2 Datacenter': 'Windows Server 2012 R2 Datacenter',
        'Windows Server 2008 R2 Enterprise': 'Windows Server 2008 R2 Enterprise',
        
        # Windows 7
        'Windows 7 Ultimate': 'Windows 7 Ultimate',
        'Windows 7 Professional': 'Windows 7 Professional',
        'Windows 7 Enterprise': 'Windows 7 Enterprise',
        
        # Linux e outros
        'Linux': 'Linux',
        'Ubuntu': 'Linux',
        'CentOS': 'Linux',
        'Red Hat': 'Linux',
    }
    
    # Busca direta primeiro
    if os_name in mappings:
        return mappings[os_name]
    
    # Busca parcial para Windows
    os_lower = os_name.lower()
    if 'windows 10' in os_lower:
        if 'enterprise' in os_lower:
            return 'Windows 10 Enterprise'
        elif 'pro' in os_lower:
            return 'Windows 10 Pro'
        else:
            return 'Windows 10 Enterprise'  # default
    elif 'windows 11' in os_lower:
        if 'enterprise' in os_lower:
            return 'Windows 11 Enterprise'
        elif 'pro' in os_lower:
            return 'Windows 11 Pro'
        else:
            return 'Windows 11 Pro'  # default
    elif 'server 2019' in os_lower:
        if 'datacenter' in os_lower:
            return 'Windows Server 2019 Datacenter'
        else:
            return 'Windows Server 2019 Standard'
    elif 'server 2022' in os_lower:
        if 'datacenter' in os_lower:
            return 'Windows Server 2022 Datacenter'
        else:
            return 'Windows Server 2022 Standard'
    elif 'server 2016' in os_lower:
        return 'Windows Server 2016 Standard'
    elif 'server 2012' in os_lower:
        if 'datacenter' in os_lower:
            return 'Windows Server 2012 R2 Datacenter'
        else:
            return 'Windows Server 2012 R2 Standard'
    elif 'server 2008' in os_lower:
        return 'Windows Server 2008 R2 Enterprise'
    elif 'windows 7' in os_lower:
        return 'Windows 7 Ultimate'
    elif 'linux' in os_lower or 'ubuntu' in os_lower or 'centos' in os_lower:
        return 'Linux'
    
    return None

def update_operating_systems():
    """Atualiza associações de sistema operacional"""
    
    # String de conexão (tentando diferentes drivers)
    drivers_to_try = [
        'ODBC Driver 18 for SQL Server',
        'ODBC Driver 17 for SQL Server',
        'SQL Server Native Client 11.0',
        'SQL Server'
    ]
    
    conn = None
    for driver in drivers_to_try:
        try:
            conn_str = (
                f'DRIVER={{{driver}}};'
                r'SERVER=10.15.2.19,1433;'
                r'DATABASE=DellReports;'
                'Trusted_Connection=yes;'
                'Encrypt=no;TrustServerCertificate=yes;'
            )
            print(f"Tentando com driver: {driver}")
            conn = pyodbc.connect(conn_str, timeout=30)
            print(f"Conectado com sucesso usando: {driver}")
            break
        except Exception as e:
            print(f"Falhou com {driver}: {e}")
            continue
    
    if not conn:
        print("Não foi possível conectar com nenhum driver")
        return False
        
    try:
        cursor = conn.cursor()
        
        # 1. Buscar computadores que precisam de atualização de SO
        print("Buscando computadores do Active Directory...")
        cursor.execute("""
            SELECT id, name, description 
            FROM computers 
            WHERE is_domain_controller = 0 
            AND operating_system_id IS NULL
            AND description IS NOT NULL
            AND description != ''
        """)
        
        computers_without_os = cursor.fetchall()
        print(f"Encontrados {len(computers_without_os)} computadores sem SO definido")
        
        # 2. Buscar todos os sistemas operacionais disponíveis
        cursor.execute("SELECT id, name, version, family FROM operating_systems ORDER BY name")
        available_os = {row[1]: row[0] for row in cursor.fetchall()}  # {name: id}
        
        print(f"Sistemas operacionais disponíveis: {len(available_os)}")
        for os_name in list(available_os.keys())[:5]:
            print(f"  - {os_name}")
        print("  ...")
        
        # 3. Processar cada computador
        updated_count = 0
        created_os_count = 0
        
        for computer in computers_without_os:
            computer_id, computer_name, description = computer
            
            if not description:
                continue
                
            # Tentar extrair SO da descrição
            normalized_os = normalize_os_name(description)
            
            if not normalized_os:
                print(f"  {computer_name}: SO não reconhecido '{description}'")
                continue
            
            os_id = None
            
            # Verificar se o SO já existe
            if normalized_os in available_os:
                os_id = available_os[normalized_os]
            else:
                # Criar novo registro de SO
                print(f"  Criando novo SO: {normalized_os}")
                cursor.execute("""
                    INSERT INTO operating_systems (name, version, architecture, family, is_server, created_at)
                    VALUES (?, NULL, 'x64', 
                           CASE WHEN ? LIKE '%Server%' THEN 'Server' 
                                WHEN ? LIKE '%Linux%' THEN 'Linux'
                                ELSE 'Windows' END,
                           CASE WHEN ? LIKE '%Server%' THEN 1 ELSE 0 END,
                           GETDATE())
                """, normalized_os, normalized_os, normalized_os, normalized_os)
                
                # Buscar o ID criado
                cursor.execute("SELECT @@IDENTITY")
                os_id = cursor.fetchone()[0]
                available_os[normalized_os] = os_id
                created_os_count += 1
                print(f"    Criado com ID: {os_id}")
            
            # Atualizar o computador
            if os_id:
                cursor.execute("""
                    UPDATE computers 
                    SET operating_system_id = ? 
                    WHERE id = ?
                """, os_id, computer_id)
                
                updated_count += 1
                print(f"  {computer_name}: associado a '{normalized_os}' (ID: {os_id})")
        
        # 4. Commit das mudanças
        conn.commit()
        print(f"\nResumo:")
        print(f"  - Computadores atualizados: {updated_count}")
        print(f"  - Novos SOs criados: {created_os_count}")
        
        cursor.close()
        conn.close()
        print("Atualização concluída com sucesso!")
        
        return True
        
    except Exception as e:
        print(f"Erro durante atualização: {e}")
        return False

if __name__ == "__main__":
    print("Iniciando atualização de sistemas operacionais...\n")
    
    success = update_operating_systems()
    
    if success:
        print("\nAtualização concluída com sucesso!")
        print("Agora os computadores devem mostrar seus sistemas operacionais corretamente.")
        sys.exit(0)
    else:
        print("\nAtualização falhou!")
        sys.exit(1)