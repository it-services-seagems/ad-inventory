#!/usr/bin/env python3
"""
Script simples para testar o endpoint de usuário por service tag via HTTP
"""
import requests
import json
import sys

API_BASE = "http://10.15.2.19:42057/api"

def test_api_endpoint():
    """Testa o endpoint via HTTP"""
    print("🌐 Testando endpoint via HTTP...")
    
    # Service tags de teste
    test_service_tags = ["C1WSB92", "1750160786", "INVALID_TAG"]
    
    for service_tag in test_service_tags:
        print(f"\n📋 Testando service tag: {service_tag}")
        
        try:
            url = f"{API_BASE}/computers/user-by-service-tag/{service_tag}"
            print(f"  📡 URL: {url}")
            
            response = requests.get(url, timeout=10)
            
            print(f"  📊 Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print(f"  ✅ Sucesso!")
                    print(f"  📱 Máquina: {data.get('computer_name')}")
                    print(f"  👤 Usuário: {data.get('usuario_atual', 'Não informado')}")
                else:
                    print(f"  ❌ Falhou: {data.get('message')}")
            elif response.status_code == 404:
                print(f"  ❌ Não encontrado")
            else:
                print(f"  ⚠️ Erro HTTP: {response.status_code}")
                print(f"  📄 Resposta: {response.text[:200]}")
                
        except requests.exceptions.RequestException as e:
            print(f"  💥 Erro na requisição: {e}")
        except Exception as e:
            print(f"  🐛 Erro: {e}")

if __name__ == "__main__":
    print("🚀 Testando endpoint de usuário por service tag\n")
    test_api_endpoint()
    print("\n🏁 Teste concluído")