#!/usr/bin/env python3
"""
Script de debug para identificar problemas na sincronização de OS
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi_app.managers import ad_manager, sql_manager
import logging

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def debug_os_sync():
    print("🔍 DEBUG: Sincronização de OS")
    print("="*50)
    
    try:
        # 1. Testar busca do AD
        print("\n1. Testando busca de computadores do AD...")
        computers = ad_manager.get_computers()
        print(f"   ✅ Encontrados {len(computers)} computadores")
        
        # Mostrar alguns exemplos
        for i, computer in enumerate(computers[:3]):
            name = computer.get('name', 'unknown')
            os_info = computer.get('os', 'unknown')  # Campo correto
            print(f"   - {name}: {os_info}")
        
        # 2. Testar conexão SQL
        print("\n2. Testando conexão SQL...")
        conn = sql_manager.get_connection()
        print(f"   ✅ Conexão obtida: {type(conn)}")
        
        # 3. Testar query de contagem antes
        print("\n3. Verificando computadores no SQL antes...")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM computers WHERE operating_system_id IS NOT NULL")
        before_count = cursor.fetchone()[0]
        print(f"   📊 Computadores com OS antes: {before_count}")
        cursor.close()
        
        # 4. Testar mapeamento de OS
        print("\n4. Testando mapeamento de OS...")
        test_computer = computers[0] if computers else None
        if test_computer:
            os_name = test_computer.get('os')  # Campo correto
            os_version = test_computer.get('osVersion')  # Campo correto
            
            print(f"   Testando: {os_name} / {os_version}")
            
            if os_name:
                os_id = sql_manager.get_or_create_operating_system(os_name, os_version)
                print(f"   ✅ Mapeado para ID: {os_id}")
                
                # Testar update individual
                cursor = conn.cursor()
                update_query = """
                UPDATE computers 
                SET operating_system_id = ?,
                    last_sync_ad = GETDATE(),
                    updated_at = GETDATE()
                WHERE name = ?
                """
                cursor.execute(update_query, os_id, test_computer.get('name'))
                rows_affected = cursor.rowcount
                print(f"   📝 Update executado, linhas afetadas: {rows_affected}")
                
                conn.commit()
                print(f"   ✅ Commit realizado")
                cursor.close()
            else:
                print(f"   ❌ SO não encontrado para {test_computer.get('name')}")
            
        # 5. Verificar depois
        print("\n5. Verificando computadores no SQL depois...")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM computers WHERE operating_system_id IS NOT NULL")
        after_count = cursor.fetchone()[0]
        print(f"   📊 Computadores com OS depois: {after_count}")
        print(f"   📈 Diferença: {after_count - before_count}")
        cursor.close()
        
    except Exception as e:
        print(f"❌ Erro no debug: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_os_sync()