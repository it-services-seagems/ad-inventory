from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from ..managers.dell import dell_api

warranty_router = APIRouter()


@warranty_router.get('/warranty/{service_tag}')
def get_warranty(service_tag: str):
    try:
        if dell_api is None:
            raise HTTPException(status_code=503, detail='Dell API client not available')
        res = dell_api.get_warranty_info(service_tag)
        if res is None or 'error' in res:
            # map some error codes to HTTP statuses
            code = res.get('code') if isinstance(res, dict) else None
            if code == 'SERVICE_TAG_NOT_FOUND':
                raise HTTPException(status_code=404, detail=res)
            elif code == 'AUTH_ERROR':
                raise HTTPException(status_code=401, detail=res)
            else:
                raise HTTPException(status_code=400, detail=res)
        return JSONResponse(content=res)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@warranty_router.post('/warranty/bulk-refresh')
def bulk_refresh(payload: dict):
    try:
        tags = payload.get('service_tags') or []
        if dell_api is None:
            raise HTTPException(status_code=503, detail='Dell API client not available')
        results = dell_api.get_warranty_info_bulk(tags)
        return JSONResponse(content={"results": results})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@warranty_router.get('/warranty-summary')
def warranty_summary():
    """Compatibility endpoint expected by the frontend: returns a list of warranty summaries.
    If the Dell client is not configured, returns an empty list with 200 to avoid frontend 404s.
    """
    try:
        if dell_api is None:
            return []

        # If the client exposes a summary method, call it; otherwise return empty list
        if hasattr(dell_api, 'get_warranty_summary'):
            return dell_api.get_warranty_summary()

        return []
    except Exception:
        # don't expose internal errors to the frontend here; return empty list
        return []


@warranty_router.get('/warranties/from-database')
def get_warranties_from_database():
    """Get existing warranty information from SQL database"""
    try:
        from ..managers.sql import sql_manager
        
        query = """
        SELECT 
            c.name as computer_name,
            c.id as computer_id,
            dw.service_tag,
            dw.warranty_start_date,
            dw.warranty_end_date,
            dw.warranty_status,
            dw.product_line_description,
            dw.system_description,
            dw.last_updated,
            dw.cache_expires_at,
            dw.last_error,
            CASE 
                WHEN dw.cache_expires_at IS NULL OR dw.cache_expires_at < GETDATE() THEN 1
                ELSE 0
            END as needs_update
        FROM computers c
        LEFT JOIN dell_warranty dw ON c.id = dw.computer_id
        WHERE c.is_domain_controller = 0
            AND c.name IS NOT NULL
            AND LEN(c.name) >= 5
        ORDER BY c.name
        """
        
        warranties = sql_manager.execute_query(query)
        
        # Process results to include service tags extracted from computer names
        for warranty in warranties:
            if not warranty.get('service_tag'):
                # Extract service tag from computer name if not stored
                extracted_tag = sql_manager.extract_service_tag_from_computer_name(warranty['computer_name'])
                warranty['service_tag'] = extracted_tag
        
        return {
            'warranties': warranties,
            'total': len(warranties),
            'with_warranty_data': len([w for w in warranties if w.get('warranty_status')]),
            'needs_update': len([w for w in warranties if w.get('needs_update')])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching warranties from database: {str(e)}")
