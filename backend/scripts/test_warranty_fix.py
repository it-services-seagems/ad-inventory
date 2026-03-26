#!/usr/bin/env python3
"""
Script para testar a correção do erro de service_tag NULL
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi_app.managers import sql_manager

def test_warranty_save():
    print("🔍 Testando correção de service_tag NULL")
    print("="*50)
    
    # Cenários de teste
    test_cases = [
        {
            "name": "Warranty data com service_tag NULL",
            "computer_id": 999999,  # ID fictício
            "warranty_data": {
                "success": True,
                "service_tag": None,
                "warranty_status": "Active",
                "product_line_description": "Test Product"
            }
        },
        {
            "name": "Warranty data com service_tag vazio",
            "computer_id": 999998,
            "warranty_data": {
                "success": True,
                "service_tag": "",
                "warranty_status": "Active",
                "product_line_description": "Test Product"
            }
        },
        {
            "name": "Warranty data com service_tag válido",
            "computer_id": 999997,
            "warranty_data": {
                "success": True,
                "service_tag": "TEST123",
                "warranty_status": "Active",
                "product_line_description": "Test Product"
            }
        },
        {
            "name": "Warranty data de erro (sem service_tag)",
            "computer_id": 999996,
            "warranty_data": {
                "success": False,
                "code": "ERROR",
                "error": "Teste de erro"
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases):
        print(f"\n{i+1}. {test_case['name']}")
        try:
            result = sql_manager.save_warranty_to_database(
                test_case['computer_id'], 
                test_case['warranty_data']
            )
            print(f"   ✅ Resultado: {result}")
        except Exception as e:
            print(f"   ❌ Erro: {e}")
    
    # Limpar dados de teste
    print(f"\n🧹 Limpando dados de teste...")
    try:
        conn = sql_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM dell_warranty WHERE computer_id IN (999999, 999998, 999997, 999996)")
        conn.commit()
        cursor.close()
        print("   ✅ Dados de teste removidos")
    except Exception as e:
        print(f"   ⚠️ Erro na limpeza: {e}")

if __name__ == "__main__":
    test_warranty_save()