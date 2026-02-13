import threading
import time
from datetime import datetime
import logging
from ..managers import ad_manager, sql_manager

logger = logging.getLogger(__name__)


class BackgroundSyncService:
    def __init__(self):
        self.sync_thread = None
        self.sync_running = False
        self.last_sync = None

    def start_background_sync(self):
        if not self.sync_running:
            self.sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
            self.sync_thread.start()
            logger.info('🔄 Serviço de sincronização iniciado')

    def _sync_loop(self):
        self.sync_running = True
        while self.sync_running:
            try:
                self.sync_ad_to_sql()
                time.sleep(3600)
            except Exception as e:
                logger.exception('Erro na sincronização background')
                time.sleep(300)

    def sync_ad_to_sql(self):
        try:
            logger.info('🔄 Iniciando sincronização AD → SQL')
            start_time = datetime.now()
            ad_computers = ad_manager.get_computers()
            if not ad_computers:
                logger.warning('Nenhum computador encontrado no AD')
                return

            stats = {'found': len(ad_computers), 'added': 0, 'updated': 0, 'errors': 0}
            for computer in ad_computers:
                try:
                    result = sql_manager.sync_computer_to_sql(computer)
                    if result:
                        stats['updated'] += 1
                    else:
                        stats['added'] += 1
                except Exception:
                    stats['errors'] += 1

            sql_manager.log_sync_operation('incremental', 'completed', stats)
            self.last_sync = datetime.now()
            duration = (self.last_sync - start_time).total_seconds()
            logger.info(f'Sincronização concluída em {duration:.1f}s - encontrados {stats["found"]}')
        except Exception:
            logger.exception('Erro na sincronização')

    def sync_ad_to_sql_incremental(self):
        """Sincronização incremental - apenas adiciona/atualiza sem remoções"""
        try:
            logger.info('🔄 Iniciando sincronização incremental AD → SQL')
            start_time = datetime.now()
            ad_computers = ad_manager.get_computers()
            if not ad_computers:
                logger.warning('Nenhum computador encontrado no AD')
                return {'computers_found': 0, 'computers_added': 0, 'computers_updated': 0}

            stats = {'computers_found': len(ad_computers), 'computers_added': 0, 'computers_updated': 0, 'errors': 0}
            
            for computer in ad_computers:
                try:
                    result = sql_manager.sync_computer_to_sql(computer)
                    if result and result > 0:  # Se retornou um ID, foi inserção ou atualização bem-sucedida
                        # Verificar se é uma nova inserção ou atualização baseado no retorno
                        # Para simplificar, vamos considerar que sempre incrementa os adicionados
                        # (o método pode ser refinado depois para distinguir melhor)
                        stats['computers_added'] += 1
                except Exception as e:
                    stats['errors'] += 1
                    logger.error(f'Erro ao sincronizar computador {computer.get("name", "desconhecido")}: {e}')

            sql_manager.log_sync_operation('incremental', 'completed', stats)
            self.last_sync = datetime.now()
            duration = (self.last_sync - start_time).total_seconds()
            logger.info(f'Sincronização incremental concluída em {duration:.1f}s - {stats["computers_found"]} encontrados, {stats["computers_added"]} adicionados, {stats["computers_updated"]} atualizados')
            
            return stats
        except Exception as e:
            logger.exception('Erro na sincronização incremental')
            raise

    def sync_ad_to_sql_complete(self):
        """Sincronização completa - limpa SQL e reconstrói do AD"""
        try:
            logger.info('🔄 Iniciando sincronização completa AD → SQL (limpeza total)')
            start_time = datetime.now()
            
            # 1. Obter dados atuais do SQL para estatísticas
            current_computers = sql_manager.get_all_computers()
            computers_before = len(current_computers) if current_computers else 0
            
            # 2. Limpar tabela SQL
            logger.info('🗑️ Limpando tabela SQL...')
            sql_manager.clear_computers_table()
            
            # 3. Obter computadores do AD
            ad_computers = ad_manager.get_computers()
            if not ad_computers:
                logger.warning('Nenhum computador encontrado no AD')
                return {'computers_before_sync': computers_before, 'computers_deleted': computers_before, 'computers_added': 0, 'computers_after_sync': 0}

            # 4. Inserir todos os computadores do AD
            stats = {
                'computers_before_sync': computers_before,
                'computers_deleted': computers_before,
                'computers_added': 0,
                'computers_after_sync': 0,
                'errors': 0
            }
            
            for computer in ad_computers:
                try:
                    sql_manager.sync_computer_to_sql(computer)
                    stats['computers_added'] += 1
                except Exception as e:
                    stats['errors'] += 1
                    logger.error(f'Erro ao inserir computador {computer.get("name", "desconhecido")}: {e}')

            stats['computers_after_sync'] = stats['computers_added']
            
            sql_manager.log_sync_operation('complete', 'completed', stats)
            self.last_sync = datetime.now()
            duration = (self.last_sync - start_time).total_seconds()
            logger.info(f'Sincronização completa concluída em {duration:.1f}s - {stats["computers_deleted"]} removidos, {stats["computers_added"]} adicionados')
            
            return stats
        except Exception as e:
            logger.exception('Erro na sincronização completa')
            raise


# Singleton
sync_service = BackgroundSyncService()
