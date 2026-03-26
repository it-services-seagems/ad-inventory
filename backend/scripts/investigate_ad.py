#!/usr/bin/env python3
"""
Script para investigar os dados reais do AD
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi_app.managers import ad_manager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def investigate_ad_data():
    print("🔍 INVESTIGAÇÃO: Dados do AD")
    print("="*50)
    
    try:
        computers = ad_manager.get_computers()[:10]  # Apenas os primeiros 10
        
        print(f"Analisando {len(computers)} computadores...")
        
        for i, computer in enumerate(computers):
            print(f"\n--- Computador {i+1}: {computer.get('name', 'unknown')} ---")
            
            # Mostrar todos os campos disponíveis
            for key, value in computer.items():
                if 'operating' in key.lower() or 'os' in key.lower():
                    print(f"  {key}: {value}")
            
            # Mostrar todos os campos para ver o que está disponível
            print("  Todos os campos:")
            for key in sorted(computer.keys()):
                value = computer[key]
                if isinstance(value, (list, dict)):
                    print(f"    {key}: {type(value)} (tamanho: {len(value)})")
                else:
                    value_str = str(value)[:50] if value else "None"
                    print(f"    {key}: {value_str}")
                    
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    investigate_ad_data()