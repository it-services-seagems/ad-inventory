from fastapi import APIRouter, HTTPException, Body
from ..services.sql_manager import sql_manager
from ..services.ad_manager import ad_manager
from ..core.config import settings
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get('/health')
async def health():
    return {'status': 'ok', 'timestamp': __import__('datetime').datetime.utcnow().isoformat()}


@router.get('/debug/sql-test')
async def debug_sql_test():
    try:
        res = sql_manager.execute_query('SELECT 1 as ok')
        return {'success': True, 'result': res}
    except Exception as e:
        logger.exception('SQL test failed')
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/debug/ad-test')
async def debug_ad_test():
    try:
        ok = ad_manager.connect()
        if ok:
            ad_manager.disconnect()
        return {'success': ok}
    except Exception as e:
        logger.exception('AD test failed')
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/debug/full-test')
async def debug_full_test():
    try:
        sql = sql_manager.execute_query('SELECT 1 as ok')
        ad = False
        try:
            ad = ad_manager.connect()
            ad_manager.disconnect()
        except Exception:
            ad = False
        return {'sql': sql, 'ad': ad}
    except Exception as e:
        logger.exception('Full test failed')
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/system/settings')
async def system_settings():
    # Return a subset of settings for frontend
    return {
        'sql_server': settings.SQL_SERVER,
        'sql_database': settings.SQL_DATABASE,
        'dell_client_id_set': bool(settings.DELL_CLIENT_ID)
    }


@router.get('/computers/{computer_name}/details')
async def computer_details(computer_name: str):
    try:
        q = 'SELECT TOP 1 * FROM computers WHERE name = ?'
        res = sql_manager.execute_query(q, [computer_name])
        if not res:
            raise HTTPException(status_code=404, detail='Not found')
        return res[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.exception('computer_details error')
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/organizations')
async def organizations():
    try:
        res = sql_manager.execute_query('SELECT id, name, code FROM organizations ORDER BY name')
        return res
    except Exception as e:
        logger.exception('organizations error')
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/operating-systems')
async def operating_systems():
    try:
        res = sql_manager.execute_query('SELECT id, name, version FROM operating_systems ORDER BY name')
        return res
    except Exception as e:
        logger.exception('operating_systems error')
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/computers/search')
async def computers_search(q: str = None, limit: int = 50):
    try:
        if not q:
            return []
        sql = "SELECT TOP (?) * FROM computers WHERE name LIKE ? ORDER BY name"
        # Use simple paramized query
        pattern = f"%{q}%"
        res = sql_manager.execute_query("SELECT TOP ? id, name, dns_hostname FROM computers WHERE name LIKE ? ORDER BY name", [limit, pattern])
        return res
    except Exception as e:
        logger.exception('computers_search error')
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/test/simple-post')
async def test_simple_post(payload: dict = Body(...)):
    return {'received': payload}


@router.get('/test/cors')
async def test_cors():
    return {'cors': 'ok'}


@router.post('/test/toggle-simple')
async def test_toggle_simple(payload: dict = Body(...)):
    return {'toggled': payload}


@router.get('/sync/status')
async def sync_status():
    try:
        # Return last few sync logs
        res = sql_manager.execute_query('SELECT TOP 5 * FROM sync_logs ORDER BY start_time DESC')
        return {'recent_logs': res}
    except Exception as e:
        logger.exception('sync_status error')
        return {'recent_logs': []}


@router.post('/computers/bulk-action')
async def computers_bulk_action(payload: dict = Body(...)):
    # Very small placeholder for bulk actions
    return {'success': True, 'payload': payload}
