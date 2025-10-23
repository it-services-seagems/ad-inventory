from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from ..connections import require_sync_service

sync_router = APIRouter()


@sync_router.post('/computers/sync')
def trigger_sync():
    try:
        svc = require_sync_service()
        svc.sync_ad_to_sql()
        return JSONResponse(content={'status': 'sync_started'})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@sync_router.get('/sync/status')
def sync_status():
    try:
        svc = require_sync_service()
        return {
            'sync_running': getattr(svc, 'sync_running', False),
            'last_sync': getattr(svc, 'last_sync', None)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
