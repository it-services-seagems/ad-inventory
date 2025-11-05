#!/usr/bin/env python3
"""
Script para diagnosticar e corrigir problemas de conexão SQL Server
"""
import pyodbc
import os
import sys

def check_odbc_drivers():
    """Verifica drivers ODBC disponíveis"""
    print("🔍 Verificando drivers ODBC disponíveis...")
    
    try:
        drivers = pyodbc.drivers()
        print(f"✅ Encontrados {len(drivers)} drivers ODBC:")
        
        sql_drivers = []
        for driver in drivers:
            print(f"  • {driver}")
            if 'SQL Server' in driver:
                sql_drivers.append(driver)
        
        print(f"\n📊 Drivers SQL Server encontrados ({len(sql_drivers)}):")
        for driver in sql_drivers:
            print(f"  ✅ {driver}")
            
        if not sql_drivers:
            print("\n❌ Nenhum driver SQL Server encontrado!")
            print("💡 Instale um driver SQL Server:")
            print("   - ODBC Driver 17 for SQL Server")
            print("   - ODBC Driver 18 for SQL Server")
            return None
            
        # Recomendar o melhor driver
        preferred = None
        for pref in ['ODBC Driver 18 for SQL Server', 'ODBC Driver 17 for SQL Server', 'SQL Server Native Client 11.0']:
            if pref in sql_drivers:
                preferred = pref
                break
                
        if preferred:
            print(f"\n🎯 Driver recomendado: {preferred}")
            return preferred
        else:
            print(f"\n🎯 Usando primeiro driver disponível: {sql_drivers[0]}")
            return sql_drivers[0]
            
    except Exception as e:
        print(f"❌ Erro ao verificar drivers: {e}")
        return None

def test_connection_string(driver_name):
    """Testa uma string de conexão"""
    from backend.fastapi_app.config import SQL_SERVER, SQL_DATABASE, SQL_USERNAME, SQL_PASSWORD, USE_WINDOWS_AUTH
    
    print(f"\n🔗 Testando conexão com driver: {driver_name}")
    
    # Tentar diferentes configurações de encrypt/trust
    configurations = [
        {'encrypt': 'no', 'trust': 'yes'},
        {'encrypt': 'yes', 'trust': 'yes'},
        {'encrypt': 'optional', 'trust': 'yes'},
    ]
    
    for config in configurations:
        try:
            if USE_WINDOWS_AUTH:
                conn_str = (
                    f"DRIVER={{{driver_name}}};"
                    f"SERVER={SQL_SERVER};"
                    f"DATABASE={SQL_DATABASE};"
                    f"Trusted_Connection=yes;"
                    f"Encrypt={config['encrypt']};"
                    f"TrustServerCertificate={config['trust']};"
                )
            else:
                conn_str = (
                    f"DRIVER={{{driver_name}}};"
                    f"SERVER={SQL_SERVER};"
                    f"DATABASE={SQL_DATABASE};"
                    f"UID={SQL_USERNAME};"
                    f"PWD={SQL_PASSWORD};"
                    f"Encrypt={config['encrypt']};"
                    f"TrustServerCertificate={config['trust']};"
                )
            
            print(f"  🔧 Testando: Encrypt={config['encrypt']}, Trust={config['trust']}")
            
            with pyodbc.connect(conn_str, timeout=5) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                
                if result and result[0] == 1:
                    print(f"  ✅ Conexão bem-sucedida!")
                    print(f"  🎯 String de conexão funcional:")
                    print(f"     {conn_str}")
                    return conn_str
                    
        except Exception as e:
            print(f"  ❌ Falhou: {e}")
            continue
    
    print(f"  💥 Todas as configurações falharam para {driver_name}")
    return None

def create_fix_script(working_conn_str, driver_name):
    """Cria um script de correção"""
    script_content = f'''# SQL Server Connection Fix
# Driver detectado automaticamente: {driver_name}

# Adicione estas variáveis de ambiente ao seu .env:
SQL_ODBC_DRIVER="{driver_name}"
SQL_ODBC_ENCRYPT="no"
SQL_ODBC_TRUST="yes"

# String de conexão funcional encontrada:
# {working_conn_str}
'''
    
    with open('.env.sql_fix', 'w') as f:
        f.write(script_content)
    
    print(f"\n📄 Arquivo de correção criado: .env.sql_fix")
    print("💡 Copie as variáveis para seu arquivo .env principal")

if __name__ == "__main__":
    print("🚀 Diagnóstico de Conexão SQL Server\n")
    
    # Verificar drivers disponíveis
    best_driver = check_odbc_drivers()
    
    if not best_driver:
        print("\n❌ Não foi possível encontrar drivers SQL Server")
        sys.exit(1)
    
    # Testar conexão
    working_conn = test_connection_string(best_driver)
    
    if working_conn:
        print(f"\n✅ Conexão SQL Server funcionando!")
        create_fix_script(working_conn, best_driver)
    else:
        print(f"\n❌ Não foi possível estabelecer conexão SQL Server")
        print("💡 Verifique:")
        print("   - Servidor SQL está acessível")
        print("   - Credenciais estão corretas") 
        print("   - Firewall permite conexão")
        sys.exit(1)
    
    print(f"\n🏁 Diagnóstico concluído")