from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional
import logging
from datetime import datetime, date

from ..managers import sql_manager

logger = logging.getLogger(__name__)

mobiles_router = APIRouter()


def serialize_datetime(obj):
    """Convert datetime objects to string for JSON serialization"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    return obj


def prepare_rows_for_json(rows):
    """Prepare database rows for JSON serialization by converting datetime fields"""
    if not rows:
        return rows
    
    serialized_rows = []
    for row in rows:
        if isinstance(row, dict):
            serialized_row = {}
            for key, value in row.items():
                serialized_row[key] = serialize_datetime(value)
            serialized_rows.append(serialized_row)
        else:
            serialized_rows.append(row)
    
    return serialized_rows


def _table_exists(table_name: str) -> bool:
    try:
        # Try selecting top 0 to inspect columns
        conn = sql_manager.get_connection()
        cur = conn.cursor()
        cur.execute(f"SELECT TOP 0 * FROM {table_name}")
        cols = [c[0] for c in cur.description] if cur.description else []
        conn.close()
        return len(cols) > 0
    except Exception:
        return False


@mobiles_router.get('/')
def list_mobiles(limit: Optional[int] = Query(100, ge=1), search: Optional[str] = None):
    """List mobiles from the database table `mobiles` if present."""
    try:
        if not _table_exists('mobiles'):
            return JSONResponse(content={
                'success': False,
                'message': 'Table `mobiles` not found in database. Create table or run migration.'
            }, status_code=404)

        # SQL Server does not accept a parameter for TOP; inject the integer safely
        try:
            top_n = int(limit) if limit is not None else 100
        except Exception:
            top_n = 100
        base_q = f"SELECT TOP {top_n} * FROM mobiles"
        rows = sql_manager.execute_query(base_q)

        # Simple search filter in-memory if requested
        if search and rows:
            q = search.lower()
            rows = [r for r in rows if any(q in (str(v) or '').lower() for v in r.values())]

        # Prepare rows for JSON serialization
        serialized_rows = prepare_rows_for_json(rows)
        
        return JSONResponse(content={'success': True, 'mobiles': serialized_rows, 'count': len(serialized_rows)})
    except Exception as e:
        logger.exception('Error listing mobiles')
        raise HTTPException(status_code=500, detail=str(e))


@mobiles_router.get('/{mobile_id}')
def mobile_detail(mobile_id: int):
    try:
        if not _table_exists('mobiles'):
            raise HTTPException(status_code=404, detail='Table `mobiles` not found')

        q = "SELECT TOP 1 * FROM mobiles WHERE id = ?"
        rows = sql_manager.execute_query(q, params=(mobile_id,))
        if not rows:
            raise HTTPException(status_code=404, detail='Mobile not found')
        
        # Prepare row for JSON serialization
        serialized_rows = prepare_rows_for_json(rows)
        
        return JSONResponse(content={'success': True, 'mobile': serialized_rows[0]})
    except HTTPException:
        raise
    except Exception as e:
        logger.exception('Error fetching mobile detail')
        raise HTTPException(status_code=500, detail=str(e))


@mobiles_router.post('/')
def create_mobile(payload: dict):
    try:
        if not _table_exists('mobiles'):
            raise HTTPException(status_code=404, detail='Table `mobiles` not found')

        # Build insert dynamically from provided keys that match columns
        conn = sql_manager.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT TOP 0 * FROM mobiles")
        columns = [c[0] for c in cur.description] if cur.description else []
        allowed = [c for c in columns if c.lower() != 'id']

        to_insert = {k: v for k, v in payload.items() if k in allowed}
        if not to_insert:
            raise HTTPException(status_code=400, detail='No valid fields provided for insert')

        cols_sql = ', '.join(to_insert.keys())
        placeholders = ', '.join(['?'] * len(to_insert))
        q = f"INSERT INTO mobiles ({cols_sql}) VALUES ({placeholders})"
        cur.execute(q, tuple(to_insert.values()))
        conn.commit()
        # Attempt to fetch inserted row - best-effort using last identity
        try:
            cur.execute("SELECT TOP 1 * FROM mobiles ORDER BY id DESC")
            row = cur.fetchone()
            columns = [c[0] for c in cur.description]
            result = dict(zip(columns, row)) if row else None
            # Prepare result for JSON serialization
            if result:
                result = prepare_rows_for_json([result])[0]
        except Exception:
            result = None

        conn.close()
        return JSONResponse(content={'success': True, 'mobile': result})
    except HTTPException:
        raise
    except Exception as e:
        logger.exception('Error creating mobile')
        raise HTTPException(status_code=500, detail=str(e))


@mobiles_router.put('/{mobile_id}')
def update_mobile(mobile_id: int, payload: dict):
    try:
        if not _table_exists('mobiles'):
            raise HTTPException(status_code=404, detail='Table `mobiles` not found')

        conn = sql_manager.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT TOP 0 * FROM mobiles")
        columns = [c[0] for c in cur.description] if cur.description else []
        allowed = [c for c in columns if c.lower() != 'id']

        to_update = {k: v for k, v in payload.items() if k in allowed}
        if not to_update:
            raise HTTPException(status_code=400, detail='No valid fields provided for update')

        set_parts = ', '.join([f"{k} = ?" for k in to_update.keys()])
        q = f"UPDATE mobiles SET {set_parts} WHERE id = ?"
        params = list(to_update.values()) + [mobile_id]
        cur.execute(q, tuple(params))
        conn.commit()
        conn.close()
        return JSONResponse(content={'success': True, 'updated': True})
    except HTTPException:
        raise
    except Exception as e:
        logger.exception('Error updating mobile')
        raise HTTPException(status_code=500, detail=str(e))


@mobiles_router.delete('/{mobile_id}')
def delete_mobile(mobile_id: int):
    try:
        if not _table_exists('mobiles'):
            raise HTTPException(status_code=404, detail='Table `mobiles` not found')

        q = "DELETE FROM mobiles WHERE id = ?"
        rows = sql_manager.execute_query(q, params=(mobile_id,), fetch=False)
        return JSONResponse(content={'success': True, 'deleted': rows > 0})
    except HTTPException:
        raise
    except Exception as e:
        logger.exception('Error deleting mobile')
        raise HTTPException(status_code=500, detail=str(e))
