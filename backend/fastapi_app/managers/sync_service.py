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


# Singleton
sync_service = BackgroundSyncService()
