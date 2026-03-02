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


@sync_router.post('/computers/sync-operating-systems')
def force_update_operating_systems():
    """Força atualização dos sistemas operacionais de todos os computadores"""
    try:
        from ..managers.sql import sql_manager
        from ..managers.ad import ad_manager
        
        # Buscar todos os computadores do AD
        computers = ad_manager.get_computers()
        
        updated_count = 0
        error_count = 0
        
        for computer in computers:
            try:
                # Mapear sistema operacional
                operating_system_id = None
                os_name = computer.get('os')  # Campo correto do AD
                os_version = computer.get('osVersion')  # Campo correto do AD
                
                if os_name:
                    operating_system_id = sql_manager.get_or_create_operating_system(
                        os_name,
                        os_version
                    )
                
                # Atualizar apenas o operating_system_id
                if operating_system_id:
                    update_query = """
                    UPDATE computers 
                    SET operating_system_id = ?,
                        last_sync_ad = GETDATE(),
                        updated_at = GETDATE()
                    WHERE name = ?
                    """
                    
                    rows_affected = sql_manager.execute_query(
                        update_query, 
                        [operating_system_id, computer['name']], 
                        fetch=False
                    )
                    
                    if rows_affected > 0:
                        updated_count += 1
                        
            except Exception as e:
                error_count += 1
                print(f"Erro ao atualizar SO para {computer.get('name', 'unknown')}: {e}")
                continue
        
        return JSONResponse(content={
            'success': True,
            'message': f'Atualização de sistemas operacionais concluída',
            'updated_computers': updated_count,
            'errors': error_count,
            'total_processed': len(computers)
        })
        
    except Exception as e:
        return JSONResponse(
            status_code=500, 
            content={
                'success': False,
                'message': f'Erro na atualização de sistemas operacionais: {str(e)}'
            }
        )
