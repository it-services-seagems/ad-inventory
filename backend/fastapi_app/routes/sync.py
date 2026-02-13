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


@sync_router.post('/computers/sync-incremental')
def trigger_sync_incremental():
    """Sincronização incremental - apenas adiciona/atualiza sem remoções"""
    try:
        svc = require_sync_service()
        result = svc.sync_ad_to_sql_incremental()
        return JSONResponse(content={
            'success': True,
            'message': 'Sincronização incremental concluída',
            'stats': result
        })
    except Exception as e:
        return JSONResponse(
            status_code=500, 
            content={
                'success': False,
                'message': f'Erro na sincronização incremental: {str(e)}'
            }
        )


@sync_router.post('/computers/sync-complete')
def trigger_sync_complete():
    """Sincronização completa - limpa SQL e reconstrói do AD"""
    try:
        svc = require_sync_service()
        result = svc.sync_ad_to_sql_complete()
        return JSONResponse(content={
            'success': True,
            'message': 'Sincronização completa concluída',
            'stats': result
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                'success': False,
                'message': f'Erro na sincronização completa: {str(e)}'
            }
        )


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
