"""Connection adapters for SQL, AD and external services.
This module will try to reuse the global instances defined in `backend.app` when
available. It also exposes a helper function `test_all_connections()` which
performs lightweight checks and returns a status dictionary. The FastAPI
startup event calls that helper and prints results to the console.
"""

import importlib
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Global holders for manager instances (may be reused from backend.app)
## Prefer local managers under fastapi_app.managers
from . import managers as local_managers

sql_manager = getattr(local_managers, 'sql_manager', None)
ad_manager = getattr(local_managers, 'ad_manager', None)
ad_computer_manager = getattr(local_managers, 'ad_computer_manager', None)
from .managers import dell as dell_module
dell_api = getattr(dell_module, 'dell_api', None)
dhcp_manager = None
sync_service = None


def _load_from_backend_app():
    global sql_manager, ad_manager, ad_computer_manager, dell_api, dhcp_manager, sync_service
    try:
        mod = importlib.import_module('backend.app')
        # Only set backend.app managers when local ones are not present
        if sql_manager is None:
            sql_manager = getattr(mod, 'sql_manager', None)
        if ad_manager is None:
            ad_manager = getattr(mod, 'ad_manager', None)
        if ad_computer_manager is None:
            ad_computer_manager = getattr(mod, 'ad_computer_manager', None)
        dell_api = getattr(mod, 'dell_api', None)
        if dhcp_manager is None:
            dhcp_manager = getattr(mod, 'dhcp_manager', None)
        if sync_service is None:
            sync_service = getattr(mod, 'sync_service', None)
        logger.info('Loaded backend.app managers (local managers preserved when available)')
    except Exception as e:
        # Log full exception with traceback to help debugging why backend.app can't be imported
        logger.exception('Could not import backend.app when attempting to reuse legacy managers')


# Try loading on import
_load_from_backend_app()


def require_sql_manager():
    if sql_manager is None:
        raise RuntimeError('SQL manager not available. Import backend.app or configure a SQL manager instance.')
    return sql_manager


def require_ad_manager():
    if ad_manager is None:
        raise RuntimeError('AD manager not available. Import backend.app or configure an AD manager instance.')
    return ad_manager


def require_ad_computer_manager():
    if ad_computer_manager is None:
        raise RuntimeError('AD Computer manager not available. Import backend.app or configure an instance.')
    return ad_computer_manager


def require_dell_api():
    if dell_api is None:
        raise RuntimeError('Dell API client not available. Import backend.app or configure an instance.')
    return dell_api


def require_dhcp_manager():
    if dhcp_manager is None:
        raise RuntimeError('DHCP manager not available. Import backend.app or configure an instance.')
    return dhcp_manager


def require_sync_service():
    if sync_service is None:
        raise RuntimeError('Sync service not available. Import backend.app or configure an instance.')
    return sync_service


def test_all_connections() -> Dict[str, Any]:
    """Run lightweight tests for available managers and return a status map.

    The function is resilient: it will skip tests for managers that are not
    present and will capture exceptions rather than raising.
    """
    statuses: Dict[str, Any] = {}

    # SQL
    try:
        sql = sql_manager
        if sql is None:
            statuses['sql'] = {'available': False, 'message': 'sql_manager not loaded'}
        else:
            try:
                # execute a light query
                res = sql.execute_query('SELECT 1 as test')
                ok = bool(res and res[0].get('test') == 1)
                statuses['sql'] = {'available': True, 'ok': ok}
            except Exception as e:
                statuses['sql'] = {'available': True, 'ok': False, 'error': str(e)}
    except Exception as e:
        statuses['sql'] = {'available': False, 'error': str(e)}

    # AD
    try:
        ad = ad_manager
        if ad is None:
            statuses['ad'] = {'available': False, 'message': 'ad_manager not loaded'}
        else:
            try:
                connected = ad.connect()
                # unbind if a connection object exists
                try:
                    if getattr(ad, 'connection', None):
                        ad.connection.unbind()
                except Exception:
                    pass
                statuses['ad'] = {'available': True, 'connected': bool(connected)}
            except Exception as e:
                statuses['ad'] = {'available': True, 'connected': False, 'error': str(e)}
    except Exception as e:
        statuses['ad'] = {'available': False, 'error': str(e)}

    # ADComputerManager (basic find)
    try:
        adm = ad_computer_manager
        if adm is None:
            statuses['ad_computer_manager'] = {'available': False, 'message': 'ad_computer_manager not loaded'}
        else:
            # no heavy call, but check that find_computer is present
            has_find = hasattr(adm, 'find_computer')
            statuses['ad_computer_manager'] = {'available': True, 'has_find_computer': has_find}
    except Exception as e:
        statuses['ad_computer_manager'] = {'available': False, 'error': str(e)}

    # Dell API
    try:
        d = dell_api
        if d is None:
            statuses['dell_api'] = {'available': False, 'message': 'dell_api not loaded'}
        else:
            try:
                token_ok = d.ensure_valid_token()
                statuses['dell_api'] = {'available': True, 'token_valid': bool(token_ok)}
            except Exception as e:
                statuses['dell_api'] = {'available': True, 'token_valid': False, 'error': str(e)}
    except Exception as e:
        statuses['dell_api'] = {'available': False, 'error': str(e)}

    # DHCP
    try:
        dh = dhcp_manager
        if dh is None:
            statuses['dhcp'] = {'available': False, 'message': 'dhcp_manager not loaded'}
        else:
            try:
                # test first server if available
                servers = getattr(dh, 'all_servers', []) or []
                test_result = None
                if servers:
                    try:
                        test_result = dh.testar_conexao_servidor(servers[0])
                        ok = test_result is not None
                    except Exception as e:
                        ok = False
                        test_result = str(e)
                else:
                    ok = False
                statuses['dhcp'] = {'available': True, 'first_server_ok': ok}
            except Exception as e:
                statuses['dhcp'] = {'available': True, 'first_server_ok': False, 'error': str(e)}
    except Exception as e:
        statuses['dhcp'] = {'available': False, 'error': str(e)}

    # Sync service
    try:
        ss = sync_service
        if ss is None:
            statuses['sync_service'] = {'available': False, 'message': 'sync_service not loaded'}
        else:
            statuses['sync_service'] = {'available': True, 'running': getattr(ss, 'sync_running', False)}
    except Exception as e:
        statuses['sync_service'] = {'available': False, 'error': str(e)}

    return statuses
