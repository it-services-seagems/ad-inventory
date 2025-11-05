#!/usr/bin/env python3
"""
Script para testar a nova funcionalidade de buscar usuário por service tag
"""
import sys
import os

# Adicionar o diretório do projeto ao Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from fastapi_app.managers.sql import sql_manager
except ImportError as e:
    print(f"❌ Erro ao importar sql_manager: {e}")
    print("Certifique-se que o ambiente virtual 'api' está ativo")
    sys.exit(1)

def test_user_by_service_tag():
    """Testa a funcionalidade de buscar usuário por service tag"""
    print("🔍 Testando busca de usuário por service tag...")
    
    # Testar com alguns service tags conhecidos
    test_service_tags = [
        "C1WSB92",  # Service tag de exemplo
        "1750160786",  # Outro service tag de exemplo
        "INVALID_TAG"  # Tag inválida para testar erro
    ]
    
    for service_tag in test_service_tags:
        print(f"\n📋 Testando service tag: {service_tag}")
        try:
            result = sql_manager.get_current_user_by_service_tag(service_tag)
            
            if result.get('found'):
                print(f"  ✅ Encontrado!")
                print(f"  📱 Máquina: {result.get('computer_name')}")
                print(f"  👤 Usuário atual: {result.get('usuario_atual') or 'Não informado'}")
                print(f"  👤 Usuário anterior: {result.get('usuario_anterior') or 'Não informado'}")
                print(f"  📝 Descrição: {result.get('description') or 'Sem descrição'}")
                if result.get('last_logon'):
                    print(f"  🕐 Último logon: {result.get('last_logon')}")
            else:
                print(f"  ❌ Não encontrado: {result.get('message', 'Erro desconhecido')}")
                if result.get('error'):
                    print(f"  🐛 Erro: {result.get('error')}")
                    
        except Exception as e:
            print(f"  💥 Erro na busca: {e}")

def test_computers_with_users():
    """Testa se a lista de computadores agora inclui os campos de usuário"""
    print("\n🔍 Testando se os computadores incluem campos de usuário...")
    
    try:
        computers = sql_manager.get_computers_from_sql()
        
        if not computers:
            print("❌ Nenhum computador encontrado")
            return False
            
        print(f"✅ Encontrados {len(computers)} computadores")
        
        # Verificar se os campos de usuário estão presentes
        computers_with_users = []
        for computer in computers[:10]:  # Verificar apenas os primeiros 10
            if computer.get('usuarioAtual'):
                computers_with_users.append({
                    'name': computer.get('name'),
                    'usuario_atual': computer.get('usuarioAtual'),
                    'usuario_anterior': computer.get('usuarioAnterior')
                })
        
        print(f"\n📊 Computadores com usuário atual definido:")
        for comp in computers_with_users:
            print(f"  • {comp['name']}: {comp['usuario_atual']}")
            if comp['usuario_anterior']:
                print(f"    Anterior: {comp['usuario_anterior']}")
        
        if computers_with_users:
            print(f"\n✅ {len(computers_with_users)} computadores têm usuário atual definido!")
        else:
            print(f"\n⚠️ Nenhum computador tem usuário atual definido")
            
        return True
            
    except Exception as e:
        print(f"❌ Erro ao testar: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando testes da funcionalidade de usuário por service tag\n")
    
    # Teste 1: Buscar usuário por service tag
    test_user_by_service_tag()
    
    # Teste 2: Verificar se lista de computadores inclui campos de usuário
    success = test_computers_with_users()
    
    print(f"\n🎯 Testes {'concluídos com sucesso' if success else 'falharam'}")
    sys.exit(0 if success else 1)