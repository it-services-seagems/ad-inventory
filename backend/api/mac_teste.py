from pypsrp.client import Client
import re
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')
logger = logging.getLogger()
logging.getLogger('pypsrp').setLevel(logging.WARNING)

def testar_conexao_servidor(servidor, usuario, senha):
    """Testa conexão com um servidor específico"""
    try:
        client = Client(
            server=servidor,
            username=usuario,
            password=senha,
            ssl=False,
            cert_validation=False,
            connection_timeout=15,
            operation_timeout=15
        )
        
        # Teste simples
        script = "Write-Output 'OK'"
        output, streams, had_errors = client.execute_ps(script)
        
        if had_errors or 'OK' not in output:
            return None
            
        return client
        
    except Exception as e:
        logger.warning(f"Falha ao conectar em {servidor}: {str(e)[:100]}")
        return None

def buscar_service_tag_servidor(servidor, usuario, senha, service_tag, prefixos=None):
    """Busca service tag em um servidor específico"""
    resultado = {
        'servidor': servidor,
        'status': 'erro',
        'entradas': {},
        'erro': None,
        'tempo': 0
    }
    
    inicio = time.time()
    
    try:
        # Conectar ao servidor
        client = testar_conexao_servidor(servidor, usuario, senha)
        if not client:
            resultado['status'] = 'conexao_falhou'
            resultado['erro'] = 'Não foi possível conectar'
            return resultado
        
        logger.info(f"✅ Conectado em {servidor}")
        
        # Preparar padrões de busca
        patterns = [service_tag]  # Service tag pura
        
        if prefixos:
            # Adicionar prefixos
            for prefixo in prefixos:
                patterns.extend([
                    f"{prefixo}-{service_tag}",      # SHQ-C1WSB92
                    f"{prefixo}_{service_tag}",      # SHQ_C1WSB92
                    f"{prefixo} {service_tag}",      # SHQ C1WSB92
                    f"{prefixo}{service_tag}",       # SHQC1WSB92
                ])
        
        # Script PowerShell otimizado para buscar múltiplos padrões
        patterns_str = "', '".join(patterns)
        script = f"""
        $patterns = @('{patterns_str}')
        $filters = Get-DhcpServerv4Filter -List Allow
        $found = @()
        
        foreach ($pattern in $patterns) {{
            $matches = $filters | Where-Object {{$_.Description -like "*$pattern*"}}
            if ($matches) {{
                $found += $matches
            }}
        }}
        
        # Remover duplicatas
        $unique = $found | Sort-Object MacAddress -Unique
        
        if ($unique) {{
            foreach ($filter in $unique) {{
                Write-Output "MAC:$($filter.MacAddress)"
                Write-Output "DESC:$($filter.Description)"
                Write-Output "---"
            }}
        }} else {{
            Write-Output "NENHUM_ENCONTRADO"
        }}
        """
        
        # Executar busca
        output, streams, had_errors = client.execute_ps(script)
        
        if had_errors:
            resultado['status'] = 'erro_dhcp'
            resultado['erro'] = '; '.join([str(error) for error in streams.error])
            return resultado
        
        # Processar resultados
        if 'NENHUM_ENCONTRADO' in output:
            resultado['status'] = 'nao_encontrado'
            logger.info(f"❌ {servidor}: Nenhuma entrada encontrada")
        else:
            # Parsear resultados
            lines = output.strip().split('\n')
            entradas = {}
            current_mac = None
            
            for line in lines:
                line = line.strip()
                if line.startswith('MAC:'):
                    current_mac = line.replace('MAC:', '').strip()
                elif line.startswith('DESC:') and current_mac:
                    desc = line.replace('DESC:', '').strip()
                    entradas[current_mac] = desc
                    
                    # Identificar qual padrão foi encontrado
                    pattern_encontrado = "desconhecido"
                    for pattern in patterns:
                        if pattern.upper() in desc.upper():
                            pattern_encontrado = pattern
                            break
                    
                    logger.info(f"✅ {servidor}: MAC {current_mac} - Padrão: {pattern_encontrado}")
            
            resultado['entradas'] = entradas
            resultado['status'] = 'encontrado' if entradas else 'nao_encontrado'
    
    except Exception as e:
        resultado['status'] = 'erro'
        resultado['erro'] = str(e)
        logger.error(f"❌ Erro em {servidor}: {str(e)[:100]}")
    
    finally:
        resultado['tempo'] = time.time() - inicio
    
    return resultado

def buscar_service_tag_todos_servidores(service_tag, usuario, senha, usar_threads=True):
    """Busca service tag em todos os servidores DHCP"""
    
    # Mapeamento completo de servidores
    servidores = [
        "DIADC02",  # DIAMANTE
        "ESMDC02",  # ESMERALDA
        "JADDC02",  # JADE
        "RUBDC02",  # RUBI
        "ONIDC02",  # ONIX
        "TOPDC02",  # TOPAZIO
    ]
    
    # Prefixos possíveis baseados nos servidores
    prefixos = ["SHQ", "ESM", "DIA", "TOP", "RUB", "JAD", "ONI"]
    
    logger.info(f"🔍 Iniciando busca por '{service_tag}' em {len(servidores)} servidores")
    logger.info(f"📋 Prefixos considerados: {', '.join(prefixos)}")
    
    resultados = {}
    inicio_total = time.time()
    
    if usar_threads:
        # Busca paralela para maior velocidade
        with ThreadPoolExecutor(max_workers=6) as executor:
            # Submeter todas as tarefas
            future_to_servidor = {
                executor.submit(buscar_service_tag_servidor, servidor, usuario, senha, service_tag, prefixos): servidor
                for servidor in servidores
            }
            
            # Coletar resultados conforme completam
            for future in as_completed(future_to_servidor):
                servidor = future_to_servidor[future]
                try:
                    resultado = future.result()
                    resultados[servidor] = resultado
                except Exception as e:
                    logger.error(f"❌ Erro na thread para {servidor}: {e}")
                    resultados[servidor] = {
                        'servidor': servidor,
                        'status': 'erro',
                        'erro': str(e),
                        'entradas': {},
                        'tempo': 0
                    }
    else:
        # Busca sequencial
        for servidor in servidores:
            resultado = buscar_service_tag_servidor(servidor, usuario, senha, service_tag, prefixos)
            resultados[servidor] = resultado
    
    tempo_total = time.time() - inicio_total
    logger.info(f"⏱️ Busca concluída em {tempo_total:.2f} segundos")
    
    return resultados

def gerar_relatorio(resultados, service_tag):
    """Gera relatório formatado dos resultados"""
    print(f"\n{'=' * 80}")
    print(f"📋 RELATÓRIO DE BUSCA - SERVICE TAG: {service_tag}")
    print(f"{'=' * 80}")
    
    encontrados = {}
    total_entradas = 0
    servidores_ok = 0
    servidores_erro = 0
    
    for servidor, resultado in resultados.items():
        print(f"\n🖥️  Servidor: {servidor}")
        print("-" * 50)
        
        status = resultado['status']
        tempo = resultado['tempo']
        
        if status == 'encontrado':
            entradas = resultado['entradas']
            total_entradas += len(entradas)
            servidores_ok += 1
            
            print(f"✅ Status: {len(entradas)} entrada(s) encontrada(s) ({tempo:.2f}s)")
            
            for mac, desc in entradas.items():
                print(f"   📍 MAC: {mac}")
                print(f"      Descrição: {desc}")
                
                # Identificar prefixo encontrado
                prefixo_encontrado = "SEM_PREFIXO"
                for prefixo in ["SHQ", "ESM", "DIA", "TOP", "RUB", "JAD", "ONI"]:
                    if prefixo in desc.upper():
                        prefixo_encontrado = prefixo
                        break
                
                print(f"      Prefixo: {prefixo_encontrado}")
                print(f"      ---")
                
                # Adicionar ao consolidado
                if prefixo_encontrado not in encontrados:
                    encontrados[prefixo_encontrado] = []
                encontrados[prefixo_encontrado].append({
                    'servidor': servidor,
                    'mac': mac,
                    'descricao': desc
                })
        
        elif status == 'nao_encontrado':
            servidores_ok += 1
            print(f"ℹ️  Status: Nenhuma entrada encontrada ({tempo:.2f}s)")
        
        elif status == 'conexao_falhou':
            servidores_erro += 1
            print(f"❌ Status: Falha na conexão ({tempo:.2f}s)")
        
        else:
            servidores_erro += 1
            print(f"❌ Status: Erro - {resultado.get('erro', 'Desconhecido')} ({tempo:.2f}s)")
    
    # Resumo consolidado
    print(f"\n{'=' * 80}")
    print(f"📊 RESUMO CONSOLIDADO")
    print(f"{'=' * 80}")
    print(f"Total de entradas encontradas: {total_entradas}")
    print(f"Servidores consultados com sucesso: {servidores_ok}")
    print(f"Servidores com erro: {servidores_erro}")
    
    if encontrados:
        print(f"\n📍 ENTRADAS POR PREFIXO:")
        for prefixo, entries in encontrados.items():
            print(f"\n  {prefixo}: {len(entries)} entrada(s)")
            for entry in entries:
                print(f"    - {entry['mac']} ({entry['servidor']})")
    
    return encontrados

def main():
    """Função principal"""
    print("🔍 BUSCA DE SERVICE TAG EM TODOS OS SERVIDORES DHCP")
    print("=" * 80)
    
    # CONFIGURAÇÕES
    service_tag = "DIA5M1QKW3"     
    usuario = "SNM\\adm.itservices"      # Usuário correto
    senha = "xmZ7P@5vkKzg"             # SUA SENHA AQUI
    usar_busca_paralela = True           # True = mais rápido, False = sequencial
    
    if senha == "sua_senha_aqui":
        print("❌ CONFIGURE SUA SENHA NO CÓDIGO!")
        return
    
    print(f"Service Tag: {service_tag}")
    print(f"Usuário: {usuario}")
    print(f"Busca paralela: {'Sim' if usar_busca_paralela else 'Não'}")
    print(f"Prefixos considerados: SHQ, ESM, DIA, TOP, RUB, JAD, ONI")
    
    # Executar busca
    resultados = buscar_service_tag_todos_servidores(
        service_tag, usuario, senha, usar_busca_paralela
    )
    
    # Gerar relatório
    encontrados = gerar_relatorio(resultados, service_tag)
    
    # Salvar resultados em arquivo (opcional)
    try:
        with open(f"busca_{service_tag}_{int(time.time())}.txt", 'w', encoding='utf-8') as f:
            f.write(f"Busca por service tag: {service_tag}\n")
            f.write(f"Data/Hora: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for servidor, resultado in resultados.items():
                f.write(f"Servidor: {servidor}\n")
                f.write(f"Status: {resultado['status']}\n")
                if resultado['entradas']:
                    for mac, desc in resultado['entradas'].items():
                        f.write(f"  MAC: {mac}\n")
                        f.write(f"  Descrição: {desc}\n\n")
                f.write("-" * 50 + "\n")
        
        print(f"\n💾 Resultados salvos em arquivo!")
        
    except Exception as e:
        print(f"⚠️  Não foi possível salvar arquivo: {e}")

if __name__ == "__main__":
    main()