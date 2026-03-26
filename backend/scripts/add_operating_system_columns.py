#!/usr/bin/env python3
"""
Script para adicionar colunas de sistema operacional na tabela computers
"""

import pyodbc
import sys

def add_operating_system_columns():
    """Adiciona colunas operating_system e operating_system_version na tabela computers"""
    
    # String de conexão para DellReports usando autenticação Windows
    conn_str = (
        'DRIVER={SQL Server};'
        r'SERVER=10.15.2.19,1433;'
        r'DATABASE=DellReports;'
        'Trusted_Connection=yes;'
    )
    
    try:
        print("🔄 Conectando ao banco de dados...")
        conn = pyodbc.connect(conn_str, timeout=10)
        cursor = conn.cursor()
        
        # Verificar se as colunas já existem
        print("🔍 Verificando colunas existentes...")
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = 'dbo' 
            AND TABLE_NAME = 'computers'
            AND COLUMN_NAME IN ('operating_system', 'operating_system_version')
        """)
        
        existing_columns = [row[0] for row in cursor.fetchall()]
        print(f"📊 Colunas de SO já existentes: {existing_columns}")
        
        # Adicionar operating_system se não existir
        if 'operating_system' not in existing_columns:
            print("➕ Adicionando coluna 'operating_system'...")
            cursor.execute("ALTER TABLE computers ADD operating_system NVARCHAR(255) NULL")
            print("✅ Coluna 'operating_system' adicionada com sucesso")
        else:
            print("✅ Coluna 'operating_system' já existe")
        
        # Adicionar operating_system_version se não existir
        if 'operating_system_version' not in existing_columns:
            print("➕ Adicionando coluna 'operating_system_version'...")
            cursor.execute("ALTER TABLE computers ADD operating_system_version NVARCHAR(255) NULL")
            print("✅ Coluna 'operating_system_version' adicionada com sucesso")
        else:
            print("✅ Coluna 'operating_system_version' já existe")
        
        # Commit das mudanças
        conn.commit()
        print("💾 Mudanças confirmadas no banco")
        
        # Verificar se precisamos popular dados existentes do AD
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM computers 
            WHERE is_domain_controller = 0 
            AND (operating_system IS NULL OR operating_system = '')
        """)
        
        empty_os_count = cursor.fetchone()[0]
        print(f"📈 Computadores sem informação de SO: {empty_os_count}")
        
        if empty_os_count > 0:
            print("⚠️  Recomendação: Execute uma sincronização do AD para popular os dados de SO")
            print("   Use: POST /api/sync/ad para sincronizar os dados")
        
        cursor.close()
        conn.close()
        print("🎉 Script executado com sucesso!")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao executar script: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando script para adicionar colunas de sistema operacional...\n")
    
    success = add_operating_system_columns()
    
    if success:
        print("\n✅ Script concluído com sucesso!")
        print("💡 Próximos passos:")
        print("   1. Reinicie a aplicação backend")
        print("   2. Execute sincronização do AD")
        print("   3. Verifique se os sistemas operacionais aparecem corretamente")
        sys.exit(0)
    else:
        print("\n❌ Script falhou!")
        sys.exit(1)