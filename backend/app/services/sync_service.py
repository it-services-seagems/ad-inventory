import threading
import time
from datetime import datetime
from .sql_manager import SQLManager
from .ad_manager import ADManager

sql_manager = SQLManager()
ad_manager = ADManager()

class BackgroundSyncService:
    def __init__(self):
        self.sync_running = False
        self.last_sync = None
        self._thread = None

    def sync_ad_to_sql(self):
        # Minimal implementation: fetch AD machines and call SQLManager.sync_computer_to_sql
        try:
            self.sync_running = True
            ad_computers = ad_manager.get_computers()
            stats = {'found': 0, 'added': 0, 'updated': 0, 'errors': 0}
            if not ad_computers:
                return stats
            stats['found'] = len(ad_computers)
            for comp in ad_computers:
                try:
                    res = sql_manager.sync_computer_to_sql(comp)
                    if res:
                        stats['updated'] += 1
                    else:
                        stats['added'] += 1
                except Exception:
                    stats['errors'] += 1
            self.last_sync = datetime.now()
            return stats
        finally:
            self.sync_running = False

    def start_background_sync(self):
        if self._thread and self._thread.is_alive():
            return
        def worker():
            while True:
                try:
                    self.sync_ad_to_sql()
                except Exception:
                    pass
                time.sleep(60 * 5)  # every 5 minutes

        self._thread = threading.Thread(target=worker, daemon=True)
        self._thread.start()


sync_service = BackgroundSyncService()
