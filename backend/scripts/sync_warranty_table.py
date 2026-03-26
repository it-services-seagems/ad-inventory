#!/usr/bin/env python3
"""
Script para sincronizar a tabela dell_warranty com todos os computadores do SQL
Atualiza os dados de garantia e modelo para cada máquina
"""

import os
import sys
import asyncio
import logging
from datetime import datetime

# Adicionar o diretório parent ao path para poder importar os módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi_app.managers.sql import SQLManager
from fastapi_app.managers.dell import DellWarrantyManager

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('warranty_sync.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

async def sync_warranty_table():
    """Sincroniza a tabela dell_warranty com todos os computadores"""
    
    sql_manager = SQLManager()
    dell_manager = DellWarrantyManager()
    
    try:
        logger.info("🔄 Iniciando sincronização da tabela dell_warranty...")
        
        # 1. Buscar todas as máquinas da tabela computers
        computers = sql_manager.get_all_computers_simple()
        logger.info(f"📊 Encontradas {len(computers)} máquinas na tabela computers")
        
        if not computers:
            logger.warning("⚠️ Nenhum computador encontrado na tabela")
            return
            
        # 2. Para cada máquina, buscar/atualizar dados de garantia
        # Filtrar máquinas que provavelmente são Dell workstations
        dell_computers = []
        for comp in computers:
            name = comp.get('name', '').upper()
            # Pular servidores e outros tipos óbvios
            skip_patterns = ['APP', 'SRV', 'SQL', 'SYNC', 'HUB', 'AV', 'FS', 'LIC', 'RM', 'RPA', 'BD', 'HML']
            should_skip = any(pattern in name for pattern in skip_patterns)
            
            # Focar em máquinas que começam com prefixos de workstation
            workstation_prefixes = ['DIA', 'TOP', 'RUB', 'ESM', 'ONI', 'JAD', 'SHQ']
            is_workstation = any(name.startswith(prefix) for prefix in workstation_prefixes)
            
            if is_workstation and not should_skip:
                dell_computers.append(comp)
        
        logger.info(f"🖥️ Máquinas Dell filtradas: {len(dell_computers)}/{len(computers)}")
        computers = dell_computers[:10]  # Processar apenas as primeiras 10 para teste
        updated_count = 0
        error_count = 0
        
        for i, computer in enumerate(computers, 1):
            computer_name = computer.get('name', '')
            computer_id = computer.get('id')
            
            if not computer_name:
                logger.warning(f"⚠️ Computador {computer_id} sem nome, pulando...")
                continue
                
            try:
                logger.info(f"🔄 [{i}/{len(computers)}] Processando: {computer_name}")
                
                # Extrair service tag do nome da máquina
                service_tag = sql_manager.extract_service_tag_from_computer_name(computer_name)
                
                if not service_tag:
                    logger.debug(f"⚠️ Não foi possível extrair service tag de: {computer_name}")
                    continue
                
                # Buscar dados de garantia da Dell
                warranty_info = await dell_manager.get_warranty_info_async(service_tag)
                
                if warranty_info and not warranty_info.get('error'):
                    # Salvar na tabela dell_warranty
                    sql_manager.save_warranty_to_database(service_tag, warranty_info)
                    updated_count += 1
                    logger.info(f"✅ {computer_name} ({service_tag}): {warranty_info.get('system_description', 'N/A')}")
                else:
                    error_count += 1
                    error_msg = warranty_info.get('error', 'Erro desconhecido') if warranty_info else 'Sem resposta da Dell'
                    logger.warning(f"❌ {computer_name} ({service_tag}): {error_msg}")
                
                # Pequeno delay para não sobrecarregar a API da Dell
                await asyncio.sleep(0.5)
                
            except Exception as e:
                error_count += 1
                logger.error(f"💥 Erro ao processar {computer_name}: {e}")
                
        # 3. Relatório final
        logger.info("=" * 60)
        logger.info(f"🎯 Sincronização concluída!")
        logger.info(f"📊 Total de máquinas: {len(computers)}")
        logger.info(f"✅ Atualizadas com sucesso: {updated_count}")
        logger.info(f"❌ Erros: {error_count}")
        logger.info(f"📝 Log salvo em: warranty_sync.log")
        
        return {
            'total': len(computers),
            'updated': updated_count,
            'errors': error_count
        }
        
    except Exception as e:
        logger.error(f"💥 Erro crítico na sincronização: {e}")
        raise

def main():
    """Função principal"""
    try:
        # Executar a sincronização
        result = asyncio.run(sync_warranty_table())
        print(f"\n🎯 Sincronização concluída: {result['updated']}/{result['total']} atualizadas")
        
    except KeyboardInterrupt:
        print("\n🛑 Sincronização interrompida pelo usuário")
        
    except Exception as e:
        print(f"\n💥 Erro: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()