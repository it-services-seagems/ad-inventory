#!/usr/bin/env python3
"""
Script para forçar atualização de todas as garantias Dell
Útil para popular a tabela dell_warranty e garantir que os modelos apareçam
"""

import sys
import os
import time
from datetime import datetime

# Adicionar o diretório backend ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from fastapi_app.managers.sql import SQLManager
from fastapi_app.managers.dell import DellWarrantyManager

# Use module logger and silence by default so script doesn't spam console unless logging is configured
logger = logging.getLogger(__name__)
try:
    logger.addHandler(logging.NullHandler())
    logger.propagate = False
except Exception:
    logger.setLevel(logging.WARNING)

def main():
    logger.info("🚀 Iniciando atualização forçada de todas as garantias...")
    
    try:
        sql_manager = SQLManager()
        dell_manager = DellWarrantyManager()
        
        # Buscar todos os computadores que têm service tag no nome
        logger.info("📋 Buscando computadores...")
        computers = sql_manager.execute_query("""
            SELECT name, id 
            FROM computers 
            WHERE name IS NOT NULL 
            AND LEN(name) > 3
            ORDER BY name
        """)
        
        if not computers:
            logger.error("❌ Nenhum computador encontrado")
            return

        logger.info(f"🔍 Encontrados {len(computers)} computadores")
        
        # Contador de progresso
        total = len(computers)
        processed = 0
        errors = 0
        updated = 0
        
        for computer in computers:
            computer_name = computer['name']
            computer_id = computer['id']
            
            try:
                # Extrair service tag do nome
                service_tag = sql_manager.extract_service_tag_from_computer_name(computer_name)
                
                if not service_tag:
                    logger.warning(f"⚠️  Pulando {computer_name} (service tag não encontrada)")
                    processed += 1
                    continue
                
                logger.info(f"🔄 [{processed+1}/{total}] Atualizando {computer_name} (ST: {service_tag})")
                
                # Forçar busca da API Dell (sempre fresh)
                warranty_info = dell_manager.get_warranty_info_force_api(service_tag)
                
                if warranty_info and not warranty_info.get('error'):
                    updated += 1
                    logger.info(f"✅ {computer_name}: {warranty_info.get('system_description', 'N/A')}")
                else:
                    errors += 1
                    error_msg = warranty_info.get('error', 'Unknown error') if warranty_info else 'No response'
                    logger.error(f"❌ {computer_name}: {error_msg}")
                
            except Exception as e:
                errors += 1
                logger.exception(f"💥 Erro ao processar {computer_name}: {e}")
            
            processed += 1
            
            # Pequena pausa para não sobrecarregar a API Dell
            if processed % 10 == 0:
                logger.info(f"⏱️  Pausa de 2s... ({processed}/{total} processados)")
                time.sleep(2)
            else:
                time.sleep(0.5)
        
        # Resumo final
        logger.info(f"\n📊 Resumo da atualização:")
        logger.info(f"   Total processados: {processed}")
        logger.info(f"   ✅ Atualizados: {updated}")
        logger.info(f"   ❌ Erros: {errors}")
        logger.info(f"   ⏭️  Pulados: {processed - updated - errors}")
        
        # Verificar quantos registros temos na tabela warranty agora
        try:
            count_result = sql_manager.execute_query("SELECT COUNT(*) as total FROM dell_warranty")
            warranty_count = count_result[0]['total'] if count_result else 0
            logger.info(f"\n🎯 Total de registros na tabela dell_warranty: {warranty_count}")
        except Exception as e:
            logger.warning(f"⚠️  Não foi possível contar registros da tabela warranty: {e}")
        
        logger.info(f"\n🏁 Atualização concluída às {datetime.now().strftime('%H:%M:%S')}")
        
    except Exception as e:
        logger.exception(f"💥 Erro geral: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    if exit_code:
        sys.exit(exit_code)