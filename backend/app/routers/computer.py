from fastapi import APIRouter, HTTPException, Query, Body
from typing import List
from ..services.sql_manager import sql_manager
from ..services.ad_manager import ad_manager
from ..services.dell_warranty import fetch_warranty_for_service_tags
from ..schemas.computer import Computer
from ..services import sql_manager as sql_manager_service
from ..services import ad_manager as ad_manager_service
from ..services import dell_warranty as dell_warranty_service
from datetime import datetime

import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/", response_model=List[Computer])
async def get_all_computers(
    source: str = Query("sql", description="Data source ('sql' or 'ad')")
):
    """
    Retrieves a list of all computers from the specified data source.
    """
    try:
        if source.lower() == 'sql':
            computers_data = sql_manager.get_computers_from_sql()
            # Pydantic will automatically validate and convert the list of dicts
            return computers_data
        elif source.lower() == 'ad':
            computers_data = ad_manager.get_computers()
            return computers_data
        else:
            raise HTTPException(status_code=400, detail="Invalid source. Must be 'sql' or 'ad'.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@router.get('/warranty-summary')
async def warranty_summary():
    try:
        query = """
        SELECT 
            dw.computer_id,
            dw.warranty_status,
            dw.warranty_start_date,
            dw.warranty_end_date,
            dw.last_updated,
            dw.last_error,
            dw.service_tag,
            dw.service_tag_clean,
            dw.product_line_description,
            dw.system_description,
            c.name as computer_name
        FROM dell_warranty dw
        INNER JOIN computers c ON dw.computer_id = c.id
        WHERE c.is_domain_controller = 0
        """
        results = sql_manager.execute_query(query)
        return results
    except Exception as e:
        logger.exception('Erro warranty_summary: %s', e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/{computer_name}/warranty/refresh')
async def refresh_warranty_for_computer(computer_name: str):
    # Use the extract logic from earlier: try fetch warranty by service tag
    try:
        service_tag = computer_name
        results = fetch_warranty_for_service_tags([service_tag], max_workers=2, batch_size=1)
        if results:
            return {'success': True, 'results': results}
        return {'success': False, 'message': 'No warranty info returned'}
    except Exception as e:
        logger.exception('Erro refresh_warranty_for_computer: %s', e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/{computer_name}/warranty')
async def get_warranty_for_computer(computer_name: str):
    """Return warranty information for a computer name (tries service tag lookup)."""
    try:
        # Try to fetch via Dell API using the computer name as service tag
        results = fetch_warranty_for_service_tags([computer_name], max_workers=2, batch_size=1)
        if not results:
            raise HTTPException(status_code=404, detail='Warranty not found')
        return results[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.exception('Erro get_warranty_for_computer: %s', e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/{computer_name}/status')
async def get_computer_status(computer_name: str):
    """Return current AD status for a computer (enabled/disabled, uac, description)."""
    try:
        if not computer_name:
            raise HTTPException(status_code=400, detail='computer_name is required')

        info = ad_manager.find_computer(computer_name)
        if not info:
            raise HTTPException(status_code=404, detail=f'Computer {computer_name} not found')

        return {
            'success': True,
            'computer': {
                'name': info.get('name'),
                'dn': info.get('dn'),
                'enabled': not info.get('disabled', False),
                'disabled': info.get('disabled', False),
                'userAccountControl': info.get('userAccountControl'),
                'description': info.get('description'),
                'operatingSystem': info.get('operatingSystem')
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception('Erro get_computer_status: %s', e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/sync')
async def sync_computers_endpoint():
    """Trigger manual sync AD -> SQL (compat with legacy /api/computers/sync)."""
    try:
        # call background sync service if available
        from ..services.sync_service import sync_service
        sync_service.sync_ad_to_sql()
        return {'status': 'success', 'message': 'Sincronização concluída', 'timestamp': datetime.now().isoformat()}
    except Exception as e:
        logger.exception('Erro sync_computers_endpoint: %s', e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/{computer_name}/toggle-status')
async def toggle_status(computer_name: str, payload: dict = Body(...)):
    action = payload.get('action')
    if action not in ['enable', 'disable']:
        raise HTTPException(status_code=400, detail="action must be 'enable' or 'disable'")

    try:
        result = ad_manager.toggle_computer_status(computer_name, action)
        return result
    except Exception as e:
        logger.exception('Erro toggle_status: %s', e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/sync-complete')
async def sync_complete():
    try:
        # Follow the original Flask logic: fetch AD computers, cleanup SQL, insert all
        ad_computers = ad_manager_service.ad_manager.get_computers()

        if not ad_computers:
            return {
                'success': False,
                'message': 'Nenhuma máquina encontrada no Active Directory'
            }

        # Stats before
        stats_before_query = """
        SELECT 
            COUNT(*) as total_before,
            SUM(CASE WHEN is_enabled = 1 THEN 1 ELSE 0 END) as enabled_before,
            SUM(CASE WHEN is_enabled = 0 THEN 1 ELSE 0 END) as disabled_before
        FROM computers 
        WHERE is_domain_controller = 0
        """
        stats_before_result = sql_manager_service.sql_manager.execute_query(stats_before_query)
        stats_before = stats_before_result[0] if stats_before_result else {}

        # Delete all non-DC computers
        cleanup_query = """
        DELETE FROM computers 
        WHERE is_domain_controller = 0
        """
        deleted_count = sql_manager_service.sql_manager.execute_query(cleanup_query, fetch=False)

        stats = {
            'found_ad': len(ad_computers),
            'total_before': stats_before.get('total_before', 0),
            'deleted': deleted_count,
            'added': 0,
            'updated': 0,
            'errors': 0
        }

        for computer in ad_computers:
            try:
                result = sql_manager_service.sql_manager.sync_computer_to_sql(computer)
                if result:
                    stats['added'] += 1
                else:
                    stats['errors'] += 1
            except Exception:
                stats['errors'] += 1

        final_stats_query = """
        SELECT 
            COUNT(*) as total_after,
            SUM(CASE WHEN is_enabled = 1 THEN 1 ELSE 0 END) as enabled_after,
            SUM(CASE WHEN is_enabled = 0 THEN 1 ELSE 0 END) as disabled_after
        FROM computers 
        WHERE is_domain_controller = 0
        """

        final_stats_result = sql_manager_service.sql_manager.execute_query(final_stats_query)
        final_stats = final_stats_result[0] if final_stats_result else {}

        response_data = {
            'success': True,
            'message': 'Sincronização completa com limpeza finalizada',
            'stats': {
                'computers_found_ad': stats['found_ad'],
                'computers_before_cleanup': stats['total_before'],
                'computers_deleted': stats['deleted'],
                'computers_added': stats['added'],
                'computers_after_sync': final_stats.get('total_after', 0),
                'enabled_after': final_stats.get('enabled_after', 0),
                'disabled_after': final_stats.get('disabled_after', 0),
                'computers_with_errors': stats['errors'],
                'total_processed': stats['found_ad']
            },
            'operation_type': 'complete_cleanup_and_rebuild',
            'timestamp': None,
            'cache_cleared': True,
            'data_refreshed': True
        }

        # Log operation
        sql_manager_service.sql_manager.log_sync_operation(
            'complete_sync_with_cleanup',
            'completed' if stats['errors'] == 0 else 'completed_with_errors',
            {
                'found': stats['found_ad'],
                'added': stats['added'],
                'updated': stats['updated'],
                'errors': stats['errors']
            }
        )

        return response_data

    except Exception as e:
        logger.exception('Erro sync_complete: %s', e)
        sql_manager_service.sql_manager.log_sync_operation('complete_sync_with_cleanup', 'failed', error_message=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/sync-incremental')
async def sync_incremental():
    try:
        # Run incremental sync directly using services (fallback logic from original flask)
        ad_computers = ad_manager_service.ad_manager.get_computers()
        stats = {'found': 0, 'added': 0, 'updated': 0, 'errors': 0}
        if ad_computers:
            stats['found'] = len(ad_computers)
            for computer in ad_computers:
                try:
                    res = sql_manager_service.sql_manager.sync_computer_to_sql(computer)
                    # sync_computer_to_sql returns True if inserted/updated
                    # We'll heuristically count as updated when existing
                    if res:
                        stats['updated'] += 1
                    else:
                        stats['added'] += 1
                except Exception:
                    stats['errors'] += 1

            sql_manager_service.sql_manager.log_sync_operation('incremental', 'completed', stats)

        return {
            'success': True,
            'message': 'Sincronização incremental concluída',
            'operation_type': 'incremental_update'
        }
    except Exception as e:
        logger.exception('Erro sync_incremental: %s', e)
        sql_manager_service.sql_manager.log_sync_operation('incremental', 'failed', error_message=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/warranty-stats')
async def warranty_stats():
    try:
        query = """
        SELECT 
            COUNT(*) as total,
            SUM(CASE 
                WHEN dw.warranty_status = 'Active' 
                    AND dw.warranty_end_date > GETDATE() 
                    AND dw.warranty_end_date > DATEADD(day, 60, GETDATE())
                THEN 1 ELSE 0 
            END) as active,
            SUM(CASE 
                WHEN dw.warranty_end_date < GETDATE() 
                THEN 1 ELSE 0 
            END) as expired,
            SUM(CASE 
                WHEN dw.warranty_end_date BETWEEN GETDATE() AND DATEADD(day, 30, GETDATE()) 
                THEN 1 ELSE 0 
            END) as expiring_30,
            SUM(CASE 
                WHEN dw.warranty_end_date BETWEEN DATEADD(day, 31, GETDATE()) AND DATEADD(day, 60, GETDATE()) 
                THEN 1 ELSE 0 
            END) as expiring_60,
            SUM(CASE 
                WHEN dw.warranty_end_date IS NULL OR dw.last_error IS NOT NULL 
                THEN 1 ELSE 0 
            END) as unknown
        FROM dell_warranty dw
        INNER JOIN computers c ON dw.computer_id = c.id
        WHERE c.is_domain_controller = 0
        """

        result = sql_manager.execute_query(query)
        stats = result[0] if result else {}

        def safe_int(v):
            try:
                return int(v) if v is not None else 0
            except Exception:
                return 0

        response = {
            'total': safe_int(stats.get('total')),
            'active': safe_int(stats.get('active')),
            'expired': safe_int(stats.get('expired')),
            'expiring_30': safe_int(stats.get('expiring_30')),
            'expiring_60': safe_int(stats.get('expiring_60')),
            'unknown': safe_int(stats.get('unknown')),
            'last_updated': datetime.now().isoformat()
        }
        return response
    except Exception as e:
        logger.exception('Erro warranty_stats: %s', e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/warranty/{computer_id}')
async def warranty_by_computer_id(computer_id: int):
    try:
        query = """
        SELECT 
            dw.*,
            c.name as computer_name,
            c.description as computer_description
        FROM dell_warranty dw
        INNER JOIN computers c ON dw.computer_id = c.id
        WHERE dw.computer_id = ?
        """
        result = sql_manager.execute_query(query, [computer_id])
        if not result:
            raise HTTPException(status_code=404, detail='Garantia não encontrada para esta máquina')

        warranty = result[0]
        # compute calculated status
        warranty_calculated_status = 'unknown'
        days_to_expiry = None
        if warranty.get('warranty_end_date') and not warranty.get('last_error'):
            try:
                end_date = warranty['warranty_end_date']
                if isinstance(end_date, str):
                    end_date = datetime.fromisoformat(end_date)
                days_to_expiry = (end_date - datetime.now()).days
                if days_to_expiry < 0:
                    warranty_calculated_status = 'expired'
                elif days_to_expiry <= 30:
                    warranty_calculated_status = 'expiring_30'
                elif days_to_expiry <= 60:
                    warranty_calculated_status = 'expiring_60'
                else:
                    warranty_calculated_status = 'active'
            except Exception:
                pass

        response = {
            'id': warranty.get('id'),
            'computer_id': warranty.get('computer_id'),
            'computer_name': warranty.get('computer_name'),
            'computer_description': warranty.get('computer_description'),
            'service_tag': warranty.get('service_tag'),
            'service_tag_clean': warranty.get('service_tag_clean'),
            'warranty_start_date': warranty.get('warranty_start_date').isoformat() if warranty.get('warranty_start_date') else None,
            'warranty_end_date': warranty.get('warranty_end_date').isoformat() if warranty.get('warranty_end_date') else None,
            'warranty_status': warranty.get('warranty_status'),
            'warranty_calculated_status': warranty_calculated_status,
            'days_to_expiry': days_to_expiry,
            'product_line_description': warranty.get('product_line_description'),
            'system_description': warranty.get('system_description'),
            'ship_date': warranty.get('ship_date'),
            'order_number': warranty.get('order_number'),
            'entitlements': warranty.get('entitlements'),
            'last_updated': warranty.get('last_updated').isoformat() if warranty.get('last_updated') else None,
            'cache_expires_at': warranty.get('cache_expires_at').isoformat() if warranty.get('cache_expires_at') else None,
            'last_error': warranty.get('last_error'),
            'created_at': warranty.get('created_at').isoformat() if warranty.get('created_at') else None
        }
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.exception('Erro warranty_by_computer_id: %s', e)
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/warranty/export')
async def export_warranty_data(format: str = Query('csv', regex='^(csv|json)$'), status: str = Query('all')):
    """Export warranty data in CSV or JSON format. Compatible with legacy /api/computers/warranty/export"""
    try:
        query = """
        SELECT 
            c.name as computer_name,
            dw.service_tag,
            dw.service_tag_clean,
            dw.warranty_status,
            dw.warranty_start_date,
            dw.warranty_end_date,
            dw.product_line_description,
            dw.system_description,
            dw.last_updated,
            dw.last_error,
            o.name as organization_name,
            o.code as organization_code,
            c.is_enabled,
            c.last_logon_timestamp,
            CASE 
                WHEN dw.warranty_end_date IS NULL THEN 'Desconhecido'
                WHEN dw.warranty_end_date < GETDATE() THEN 'Expirada'
                WHEN dw.warranty_end_date <= DATEADD(day, 30, GETDATE()) THEN 'Expirando em 30 dias'
                WHEN dw.warranty_end_date <= DATEADD(day, 60, GETDATE()) THEN 'Expirando em 60 dias'
                ELSE 'Ativa'
            END as warranty_status_calc,
            CASE 
                WHEN dw.warranty_end_date IS NOT NULL AND dw.warranty_end_date >= GETDATE()
                THEN DATEDIFF(day, GETDATE(), dw.warranty_end_date)
                ELSE NULL
            END as days_to_expiry
        FROM dell_warranty dw
        INNER JOIN computers c ON dw.computer_id = c.id
        LEFT JOIN organizations o ON c.organization_id = o.id
        WHERE c.is_domain_controller = 0
        """

        params = []
        if status != 'all':
            if status == 'active':
                query += " AND dw.warranty_end_date > DATEADD(day, 60, GETDATE())"
            elif status == 'expired':
                query += " AND dw.warranty_end_date < GETDATE()"
            elif status == 'expiring_30':
                query += " AND dw.warranty_end_date BETWEEN GETDATE() AND DATEADD(day, 30, GETDATE())"
            elif status == 'expiring_60':
                query += " AND dw.warranty_end_date BETWEEN DATEADD(day, 31, GETDATE()) AND DATEADD(day, 60, GETDATE())"

        query += " ORDER BY dw.warranty_end_date ASC, c.name"

        results = sql_manager.execute_query(query, params)

        if format == 'json':
            return {
                'count': len(results),
                'rows': results
            }

        # CSV path
        import io, csv
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        header = [
            'computer_name', 'service_tag', 'service_tag_clean', 'warranty_status',
            'warranty_start_date', 'warranty_end_date', 'product_line_description', 'system_description',
            'last_updated', 'last_error', 'organization_name', 'organization_code', 'is_enabled',
            'last_logon_timestamp', 'warranty_status_calc', 'days_to_expiry'
        ]
        writer.writerow(header)

        for row in results:
            writer.writerow([
                row.get('computer_name'),
                row.get('service_tag'),
                row.get('service_tag_clean'),
                row.get('warranty_status'),
                row.get('warranty_start_date'),
                row.get('warranty_end_date'),
                row.get('product_line_description'),
                row.get('system_description'),
                row.get('last_updated'),
                row.get('last_error'),
                row.get('organization_name'),
                row.get('organization_code'),
                row.get('is_enabled'),
                row.get('last_logon_timestamp'),
                row.get('warranty_status_calc'),
                row.get('days_to_expiry')
            ])

        csv_content = output.getvalue()
        from fastapi.responses import Response
        filename = f"warranty_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        return Response(content=csv_content, media_type='text/csv', headers={
            'Content-Disposition': f'attachment; filename="{filename}"'
        })

    except Exception as e:
        logger.exception('Erro export_warranty_data: %s', e)
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/warranty/refresh')
async def refresh_warranties(payload: dict = None):
    try:
        data = payload or {}
        max_computers = data.get('max_computers')
        only_expired = data.get('only_expired', False)
        only_errors = data.get('only_errors', False)
        workers = data.get('workers', 5)

        # Simulate in development; in production attempt to spawn script
        import os, subprocess
        script_path = os.path.join(os.path.dirname(__file__), '..', '..', 'dell_warranty_updater.py')
        if os.getenv('FLASK_ENV') == 'development' or not os.path.exists(script_path):
            return {
                'success': True,
                'message': 'Atualização de garantias iniciada em background (simulação)',
                'parameters': {'max_computers': max_computers or 'all', 'only_expired': only_expired, 'only_errors': only_errors, 'workers': workers}
            }

        try:
            cmd = ['python', script_path]
            if max_computers:
                cmd.extend(['--max-computers', str(max_computers)])
            if only_expired:
                cmd.append('--only-expired')
            if only_errors:
                cmd.append('--only-errors')
            cmd.extend(['--workers', str(workers)])

            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return {'success': True, 'message': 'Atualização iniciada', 'process_id': process.pid}
        except FileNotFoundError:
            raise HTTPException(status_code=500, detail='Script de atualização não encontrado')
    except Exception as e:
        logger.exception('Erro refresh_warranties: %s', e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/warranty/refresh-status')
async def warranty_refresh_status():
    try:
        query = """
        SELECT TOP 5
            sync_type,
            start_time,
            end_time,
            status,
            computers_found,
            computers_added,
            computers_updated,
            errors_count,
            error_message
        FROM sync_logs
        WHERE sync_type LIKE '%warranty%' OR sync_type LIKE '%dell%'
        ORDER BY start_time DESC
        """
        logs = sql_manager.execute_query(query)

        # try to find running processes
        running = []
        try:
            import psutil
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if 'dell_warranty' in ' '.join(proc.info.get('cmdline') or []):
                        running.append({'pid': proc.pid, 'name': proc.name(), 'cmdline': proc.info.get('cmdline')})
                except Exception:
                    continue
        except Exception:
            pass

        return {'last_run': logs[0] if logs else None, 'running_processes': running, 'is_running': len(running) > 0, 'recent_logs': logs}
    except Exception as e:
        logger.exception('Erro warranty_refresh_status: %s', e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/warranty/search')
async def warranty_search(status: str = 'all', organization: str = '', q: str = '', limit: int = 100, offset: int = 0):
    try:
        where_conditions = ["c.is_domain_controller = 0"]
        params = []
        if q:
            where_conditions.append("(c.name LIKE ? OR dw.service_tag LIKE ? OR dw.service_tag_clean LIKE ? OR dw.product_line_description LIKE ? OR dw.system_description LIKE ?)")
            search_pattern = f"%{q}%"
            params.extend([search_pattern]*5)
        if organization:
            where_conditions.append("o.code = ?")
            params.append(organization)
        if status != 'all':
            if status == 'active':
                where_conditions.append("dw.warranty_end_date > GETDATE() AND dw.warranty_end_date > DATEADD(day, 60, GETDATE()) AND dw.last_error IS NULL")
            elif status == 'expired':
                where_conditions.append("dw.warranty_end_date < GETDATE()")
            elif status == 'expiring_30':
                where_conditions.append("dw.warranty_end_date BETWEEN GETDATE() AND DATEADD(day, 30, GETDATE())")
            elif status == 'expiring_60':
                where_conditions.append("dw.warranty_end_date BETWEEN DATEADD(day, 31, GETDATE()) AND DATEADD(day, 60, GETDATE())")
            elif status == 'unknown':
                where_conditions.append("(dw.warranty_end_date IS NULL OR dw.last_error IS NOT NULL)")

        where_clause = " AND ".join(where_conditions)
        query = f"""
        SELECT 
            dw.computer_id,
            c.name as computer_name,
            dw.service_tag,
            dw.service_tag_clean,
            dw.warranty_start_date,
            dw.warranty_end_date,
            dw.warranty_status,
            dw.product_line_description,
            dw.system_description,
            dw.last_updated,
            dw.last_error,
            o.name as organization_name,
            o.code as organization_code,
            c.is_enabled
        FROM dell_warranty dw
        INNER JOIN computers c ON dw.computer_id = c.id
        LEFT JOIN organizations o ON c.organization_id = o.id
        WHERE {where_clause}
        ORDER BY dw.warranty_end_date ASC, c.name
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """
        params_with_pagination = params + [offset, limit]
        results = sql_manager.execute_query(query, params_with_pagination)
        count_query = f"SELECT COUNT(*) as total FROM dell_warranty dw INNER JOIN computers c ON dw.computer_id = c.id LEFT JOIN organizations o ON c.organization_id = o.id WHERE {where_clause}"
        count_result = sql_manager.execute_query(count_query, params)
        total = count_result[0]['total'] if count_result else 0

        warranties = []
        for row in results:
            warranties.append({
                'computer_id': row['computer_id'],
                'computer_name': row['computer_name'],
                'service_tag': row['service_tag'],
                'service_tag_clean': row['service_tag_clean'],
                'warranty_start_date': row['warranty_start_date'].isoformat() if row['warranty_start_date'] else None,
                'warranty_end_date': row['warranty_end_date'].isoformat() if row['warranty_end_date'] else None,
                'warranty_status': row['warranty_status'],
                'product_line_description': row['product_line_description'],
                'system_description': row['system_description'],
                'last_updated': row['last_updated'].isoformat() if row['last_updated'] else None,
                'last_error': row['last_error'],
                'organization_name': row['organization_name'],
                'organization_code': row['organization_code'],
                'is_enabled': row['is_enabled']
            })

        return {'warranties': warranties, 'total': total, 'limit': limit, 'offset': offset, 'has_more': (offset+limit) < total}
    except Exception as e:
        logger.exception('Erro warranty_search: %s', e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/warranty/debug/{computer_name}')
async def debug_warranty(computer_name: str):
    try:
        # Check DB for computer
        comp_q = "SELECT id, name, description, organization_id FROM computers WHERE name = ? AND is_domain_controller = 0"
        comp_res = sql_manager.execute_query(comp_q, [computer_name])
        debug_info = {'computer_name': computer_name, 'timestamp': datetime.now().isoformat(), 'tests': {}}
        if not comp_res:
            debug_info['tests']['computer_exists'] = {'found': False}
            return debug_info

        computer = comp_res[0]
        debug_info['tests']['computer_exists'] = {'found': True, 'computer_id': computer['id']}

        warranty_q = "SELECT * FROM dell_warranty WHERE computer_id = ?"
        warranty_res = sql_manager.execute_query(warranty_q, [computer['id']])
        if warranty_res:
            w = warranty_res[0]
            debug_info['tests']['warranty_exists'] = {'found': True, 'service_tag': w.get('service_tag'), 'warranty_status': w.get('warranty_status'), 'last_error': w.get('last_error')}
        else:
            debug_info['tests']['warranty_exists'] = {'found': False}

        # Extract service tag (simple)
        extracted = None
        if computer and computer.get('name'):
            name = computer.get('name')
            prefixes = ['SHQ','ESM','DIA','TOP','RUB','JAD','ONI','CLO']
            for p in prefixes:
                if name.upper().startswith(p):
                    extracted = name.upper()[len(p):]
                    break
        debug_info['tests']['service_tag_extraction'] = {'extracted': extracted}

        # Test Dell API call
        if extracted:
            try:
                dell = dell_warranty_service.fetch_warranty_for_service_tags([extracted], max_workers=2, batch_size=1)
                debug_info['tests']['dell_api_test'] = {'attempted': True, 'result': dell}
            except Exception as e:
                debug_info['tests']['dell_api_test'] = {'attempted': True, 'error': str(e)}

        return debug_info
    except Exception as e:
        logger.exception('Erro debug_warranty: %s', e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/warranty/export')
async def warranty_export(format: str = 'json', status: str = 'all'):
    try:
        # basic json export
        q = "SELECT c.name as computer_name, dw.service_tag, dw.service_tag_clean, dw.warranty_status, dw.warranty_start_date, dw.warranty_end_date, dw.product_line_description, dw.system_description, dw.last_updated, dw.last_error, o.name as organization_name, o.code as organization_code, c.is_enabled FROM dell_warranty dw INNER JOIN computers c ON dw.computer_id = c.id LEFT JOIN organizations o ON c.organization_id = o.id WHERE c.is_domain_controller = 0"
        results = sql_manager.execute_query(q)
        processed = []
        for row in results:
            processed.append({
                'computer_name': row.get('computer_name'),
                'service_tag': row.get('service_tag'),
                'warranty_status': row.get('warranty_status'),
                'warranty_start_date': row.get('warranty_start_date').isoformat() if row.get('warranty_start_date') else None,
                'warranty_end_date': row.get('warranty_end_date').isoformat() if row.get('warranty_end_date') else None,
                'product_line_description': row.get('product_line_description'),
                'system_description': row.get('system_description'),
                'organization_name': row.get('organization_name'),
                'organization_code': row.get('organization_code'),
                'is_enabled': row.get('is_enabled')
            })
        return {'success': True, 'data': processed, 'total_records': len(processed), 'export_date': datetime.now().isoformat(), 'status_filter': status}
    except Exception as e:
        logger.exception('Erro warranty_export: %s', e)
        raise HTTPException(status_code=500, detail=str(e))
