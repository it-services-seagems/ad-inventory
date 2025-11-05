#!/usr/bin/env python3
"""
Script para verificar se o endpoint de detalhes do computador está retornando os campos de usuário
"""
import requests
import json
import sys

API_BASE = "http://10.15.2.19:42059/api"

def test_computer_details():
    """Testa o endpoint de detalhes do computador"""
    print("🔍 Testando endpoint /computers/details...")
    
    # Tentar buscar alguns computadores
    test_computers = ["DIAC1WSB92", "SHQC1WSB92", "TOPTEST123"]
    
    for computer_name in test_computers:
        print(f"\n📋 Testando computador: {computer_name}")
        
        try:
            url = f"{API_BASE}/computers/details/{computer_name}"
            print(f"  📡 URL: {url}")
            
            response = requests.get(url, timeout=10)
            
            print(f"  📊 Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"  ✅ Dados recebidos:")
                print(f"    📱 Nome: {data.get('name', 'N/A')}")
                print(f"    💾 OS: {data.get('os', 'N/A')}")
                print(f"    👤 Usuário atual: {data.get('usuario_atual', 'N/A')}")
                print(f"    👤 Usuário anterior: {data.get('usuario_anterior', 'N/A')}")
                print(f"    🏢 Organização: {data.get('organization_name', 'N/A')}")
                
                # Verificar se os campos estão presentes
                has_user_fields = 'usuario_atual' in data or 'usuario_anterior' in data
                print(f"  🎯 Campos de usuário presentes: {'✅ Sim' if has_user_fields else '❌ Não'}")
                
            elif response.status_code == 404:
                print(f"  ❌ Computador não encontrado")
            else:
                print(f"  ⚠️ Erro HTTP: {response.status_code}")
                print(f"  📄 Resposta: {response.text[:200]}")
                
        except requests.exceptions.RequestException as e:
            print(f"  💥 Erro na requisição: {e}")
        except Exception as e:
            print(f"  🐛 Erro: {e}")

def test_computers_list():
    """Testa o endpoint de lista de computadores"""
    print(f"\n🔍 Testando endpoint /computers (lista)...")
    
    try:
        url = f"{API_BASE}/computers"
        response = requests.get(url, timeout=15)
        
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, list) and len(data) > 0:
                print(f"✅ Lista recebida com {len(data)} computadores")
                
                # Verificar alguns computadores da lista
                computers_with_users = []
                for comp in data[:10]:  # Primeiros 10
                    if comp.get('usuarioAtual'):
                        computers_with_users.append({
                            'name': comp.get('name'),
                            'usuario': comp.get('usuarioAtual'),
                            'anterior': comp.get('usuarioAnterior')
                        })
                
                print(f"📊 Computadores com usuário atual ({len(computers_with_users)}/10):")
                for comp in computers_with_users:
                    print(f"  • {comp['name']}: {comp['usuario']}")
                    if comp['anterior']:
                        print(f"    Anterior: {comp['anterior']}")
                
                if len(computers_with_users) > 0:
                    print("✅ Campos de usuário estão sendo retornados na lista")
                else:
                    print("⚠️ Nenhum computador com usuário definido encontrado")
            else:
                print("❌ Lista vazia ou formato inválido")
                
        else:
            print(f"❌ Erro HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"💥 Erro: {e}")

if __name__ == "__main__":
    print("🚀 Testando endpoints de computadores com campos de usuário\n")
    
    # Teste 1: Detalhes de computadores específicos
    test_computer_details()
    
    # Teste 2: Lista de computadores
    test_computers_list()
    
    print("\n🏁 Testes concluídos")