#!/usr/bin/env python3
"""
Script para verificar a estrutura do banco DellReports
"""

import pyodbc
import sys

def verify_database_structure():
    """Verifica a estrutura do banco DellReports"""
    
    # String de conexão para DellReports usando autenticação Windows
    conn_str = (
        'DRIVER={SQL Server};'
        r'SERVER=10.15.2.19,1433;'
        r'DATABASE=DellReports;'
        'Trusted_Connection=yes;'
    )
    
    try:
        print("Conectando ao banco de dados DellReports...")
        conn = pyodbc.connect(conn_str, timeout=10)
        cursor = conn.cursor()
        
        # Verificar se a tabela computers existe
        print("Verificando tabela computers...")
        cursor.execute("""
            SELECT COUNT(*) as table_exists
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = 'computers'
        """)
        
        computers_exists = cursor.fetchone()[0]
        print(f"Tabela computers existe: {'Sim' if computers_exists else 'Não'}")
        
        # Verificar se a tabela operating_systems existe
        print("Verificando tabela operating_systems...")
        cursor.execute("""
            SELECT COUNT(*) as table_exists
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = 'operating_systems'
        """)
        
        os_exists = cursor.fetchone()[0]
        print(f"Tabela operating_systems existe: {'Sim' if os_exists else 'Não'}")
        
        if computers_exists and os_exists:
            # Ver quantos sistemas operacionais temos
            cursor.execute("SELECT COUNT(*) FROM operating_systems")
            os_count = cursor.fetchone()[0]
            print(f"Total de sistemas operacionais cadastrados: {os_count}")
            
            # Ver alguns exemplos
            cursor.execute("SELECT TOP 5 id, name, version FROM operating_systems")
            print("Exemplos de sistemas operacionais:")
            for row in cursor.fetchall():
                print(f"  ID: {row[0]}, Nome: {row[1]}, Versao: {row[2] or 'N/A'}")
            
            # Ver quantos computadores tem SO definido
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM computers 
                WHERE is_domain_controller = 0 
                AND operating_system_id IS NOT NULL
            """)
            
            computers_with_os = cursor.fetchone()[0]
            print(f"Computadores com SO definido: {computers_with_os}")
            
            # Ver quantos computadores não tem SO
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM computers 
                WHERE is_domain_controller = 0 
                AND operating_system_id IS NULL
            """)
            
            computers_without_os = cursor.fetchone()[0]
            print(f"Computadores sem SO definido: {computers_without_os}")
            
        cursor.close()
        conn.close()
        print("Verificacao concluida!")
        
        return True
        
    except Exception as e:
        print(f"Erro ao verificar banco: {e}")
        return False

if __name__ == "__main__":
    print("Iniciando verificacao da estrutura do banco DellReports...\n")
    
    success = verify_database_structure()
    
    if success:
        print("\nVerificacao concluida com sucesso!")
        print("A estrutura do banco foi verificada.")
        print("Os sistemas operacionais devem aparecer corretamente agora.")
        sys.exit(0)
    else:
        print("\nVerificacao falhou!")
        sys.exit(1)