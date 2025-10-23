import threading
import time
import uuid
from typing import Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, BackgroundTasks, HTTPException

from ..config import settings

router = APIRouter()

# Simple in-memory job store (job_id -> status dict)
import threading as _threading

# Simple in-memory job store (job_id -> status dict)
_jobs = {}
_jobs_lock = _threading.Lock()


def _chunk_list(seq, size=100):
    for i in range(0, len(seq), size):
        yield seq[i:i + size]


def _convert_raw_to_processed(raw, service_tag):
    """Convert raw Dell API entry into the processed shape expected by the DB saver.

    This mirrors the normalization logic present in the legacy script.
    """
    try:
        entitlements = raw.get('entitlements', []) if raw else []

        warranty_start_date = None
        warranty_end_date = None

        start_dates = []
        end_dates = []
        for ent in entitlements:
            if ent.get('startDate'):
                try:
                    from datetime import datetime
                    start_dates.append(datetime.fromisoformat(ent.get('startDate').replace('Z', '+00:00')))
                except Exception:
                    pass
            if ent.get('endDate'):
                try:
                    from datetime import datetime
                    end_dates.append(datetime.fromisoformat(ent.get('endDate').replace('Z', '+00:00')))
                except Exception:
                    pass

        if start_dates:
            warranty_start_date = min(start_dates)
        if end_dates:
            warranty_end_date = max(end_dates)

        warranty_status = 'Unknown'
        if warranty_end_date:
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)
            if warranty_end_date.replace(tzinfo=timezone.utc) > now:
                warranty_status = 'Active'
            else:
                warranty_status = 'Expired'
        elif entitlements:
            warranty_status = 'Active'

        # Formato baseado no debug_c1wsb92.py
        processed = {
            'success': True,
            'service_tag': service_tag,
            'service_tag_clean': service_tag,
            'warranty_start_date': warranty_start_date,
            'warranty_end_date': warranty_end_date,
            'warranty_status': warranty_status,
            'product_line_description': raw.get('productLineDescription', '') if raw else '',
            'system_description': raw.get('systemDescription', '') if raw else '',
            'ship_date': raw.get('shipDate') if raw else None,
            'order_number': raw.get('orderNumber') if raw else None,
            'entitlements': None,
            'last_updated': datetime.now(),
            'cache_expires_at': datetime.now() + timedelta(days=7),
            'last_error': None
        }

        # Serializar entitlements como JSON (igual ao script original)
        try:
            import json
            processed['entitlements'] = json.dumps(entitlements, default=str)
        except Exception:
            processed['entitlements'] = None

        return processed
    except Exception as e:
        return {'success': False, 'error': str(e), 'code': 'PROCESS_ERROR', 'service_tag': service_tag}


@router.post("/computers/warranty-refresh")
def start_warranty_refresh(background_tasks: BackgroundTasks, mode: Optional[str] = 'full'):
    """Start a background job that refreshes Dell warranties.

    mode: 'full' will process all computers found by the legacy script. (default)
    Returns a job_id which can be polled for progress.
    """
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {
        'id': job_id,
        'status': 'pending',
        'total': 0,
        'processed': 0,
        'started_at': None,
        'ended_at': None,
        'error': None
    }

    def _job_runner(jid: str):
        try:
            # mark running in a thread-safe way
            with _jobs_lock:
                _jobs[jid]['status'] = 'running'
                _jobs[jid]['started_at'] = time.time()

            # Use the new Dell API manager instead of legacy script
            from ..managers.dell import dell_api
            from ..managers.sql import sql_manager
            import logging
            
            logger = logging.getLogger(__name__)
            logger.info(f"Starting warranty refresh job {jid}")

            # Ensure Dell API client is available before any network calls
            from ..managers import dell as _dell_module
            dell_api = getattr(_dell_module, 'dell_api', None)
            if dell_api is None:
                logger.error('Dell API client not configured; aborting warranty job')
                with _jobs_lock:
                    _jobs[jid]['status'] = 'failed'
                    _jobs[jid]['error'] = 'Dell API client not available'
                    _jobs[jid]['ended_at'] = time.time()
                return

            # Get list of computers from SQL manager (service tags already extracted in SQL)
            computers_with_tags = sql_manager.get_computers_for_warranty_update()
            logger.info(f"Retrieved {len(computers_with_tags)} computers with service tags for warranty update")
            
            # All computers already have service tags extracted efficiently in SQL
            tags = [c['service_tag'] for c in computers_with_tags]
            tag_to_computer = {c['service_tag']: c for c in computers_with_tags}
            
            logger.info(f"Processing {len(tags)} service tags: {tags[:5]}{'...' if len(tags) > 5 else ''}")

            # Processar de 10 em 10 para melhor controle de progresso
            batches = list(_chunk_list(tags, 10))
            _jobs[jid]['total'] = len(tags)
            _jobs[jid]['total_batches'] = len(batches)
            _jobs[jid]['current_batch'] = 0

            processed_count = 0
            success_count = 0
            error_count = 0
            
            for batch_idx, batch in enumerate(batches):
                batch_start_time = time.time()
                with _jobs_lock:
                    _jobs[jid]['current_batch'] = batch_idx + 1
                    _jobs[jid]['current_batch_items'] = []
                    _jobs[jid]['batch_start_time'] = batch_start_time
                
                logger.info(f"Starting batch {batch_idx + 1}/{len(batches)} with {len(batch)} items")
                
                # Process batch using the new Dell API
                for service_tag in batch:
                    try:
                        # Add delay between requests (2 seconds minimum)
                        time.sleep(2)
                        
                        # Update current processing info
                        _jobs[jid]['current_processing'] = service_tag
                        
                        # Get computer info from our optimized mapping
                        computer = tag_to_computer.get(service_tag)
                        computer_id = computer['id'] if computer else None
                        computer_name = computer['name'] if computer else 'Unknown'
                        
                        # Get warranty info using new Dell API
                        result = dell_api.get_warranty_info(service_tag)
                        
                        if result and 'error' not in result:
                            # Convert result to database format and save
                            processed = _convert_raw_to_processed(result, service_tag)
                            
                            if computer_id:
                                try:
                                    sql_manager.save_warranty_to_database(computer_id, processed)
                                    success_count += 1
                                    _jobs[jid]['current_batch_items'].append({
                                        'service_tag': service_tag,
                                        'computer_name': computer_name,
                                        'status': 'success',
                                        'warranty_status': processed.get('warranty_status'),
                                        'end_date': processed.get('warranty_end_date').strftime('%Y-%m-%d') if processed.get('warranty_end_date') else None,
                                        'product': processed.get('product_line_description', '')[:30] + '...' if processed.get('product_line_description') else ''
                                    })
                                    logger.info(f"✅ {service_tag} ({computer_name}): {processed.get('warranty_status')}")
                                except Exception as save_error:
                                    error_count += 1
                                    _jobs[jid]['current_batch_items'].append({
                                        'service_tag': service_tag,
                                        'computer_name': computer_name,
                                        'status': 'save_error',
                                        'error': str(save_error)[:50] + '...' if len(str(save_error)) > 50 else str(save_error)
                                    })
                                    logger.error(f"❌ Save error for {service_tag}: {save_error}")
                            else:
                                error_count += 1
                                _jobs[jid]['current_batch_items'].append({
                                    'service_tag': service_tag,
                                    'computer_name': computer_name,
                                    'status': 'no_computer_id',
                                    'error': 'Computer ID not found'
                                })
                                logger.warning(f"⚠️ No computer ID for {service_tag}")
                        else:
                            error_count += 1
                            error_msg = result.get('error') if result else 'No result from API'
                            _jobs[jid]['current_batch_items'].append({
                                'service_tag': service_tag,
                                'computer_name': computer_name,
                                'status': 'api_error',
                                'error': error_msg[:50] + '...' if len(str(error_msg)) > 50 else str(error_msg)
                            })
                            logger.error(f"❌ API error for {service_tag}: {error_msg}")
                        
                        processed_count += 1
                        with _jobs_lock:
                            _jobs[jid]['processed'] = processed_count
                            _jobs[jid]['success_count'] = success_count
                            _jobs[jid]['error_count'] = error_count
                            # Update progress percentage
                            _jobs[jid]['progress_percent'] = int((processed_count / len(tags)) * 100)
                        
                    except Exception as e:
                        # Continue on API errors
                        error_count += 1
                        processed_count += 1
                        _jobs[jid]['processed'] = processed_count
                        _jobs[jid]['error_count'] = error_count
                        _jobs[jid]['progress_percent'] = int((processed_count / len(tags)) * 100)
                        _jobs[jid]['current_batch_items'].append({
                            'service_tag': service_tag,
                            'computer_name': tag_to_computer.get(service_tag, {}).get('name', 'Unknown'),
                            'status': 'exception',
                            'error': str(e)[:50] + '...' if len(str(e)) > 50 else str(e)
                        })
                        logger.exception(f"❌ Exception for {service_tag}: {e}")

                # Batch completion
                batch_duration = time.time() - batch_start_time
                _jobs[jid]['last_batch_duration'] = batch_duration
                
                logger.info(f"✅ Batch {batch_idx + 1}/{len(batches)} completed in {batch_duration:.1f}s. Success: {success_count}, Errors: {error_count}")
                
                # Update batch completion status
                _jobs[jid]['batch_completed_at'] = time.time()
                
                # Brief pause between batches (reduced since we already have delays in API calls)
                time.sleep(0.5)

            with _jobs_lock:
                _jobs[jid]['status'] = 'completed'
                _jobs[jid]['ended_at'] = time.time()
        except Exception as e:
            with _jobs_lock:
                _jobs[jid]['status'] = 'failed'
                _jobs[jid]['error'] = str(e)
                _jobs[jid]['ended_at'] = time.time()

    # Start thread
    thread = threading.Thread(target=_job_runner, args=(job_id,), daemon=True)
    thread.start()

    return {'job_id': job_id}


@router.get("/computers/warranty-refresh/{job_id}")
def warranty_refresh_status(job_id: str):
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail='Job not found')

    total = job.get('total') or 0
    processed = job.get('processed') or 0
    percent = int((processed / total) * 100) if total > 0 else (100 if job.get('status') == 'completed' else 0)

    # Calculate estimated time remaining based on batch performance
    estimated_time_remaining = None
    if job.get('started_at') and processed > 0 and job.get('status') == 'running':
        elapsed_time = time.time() - job.get('started_at')
        
        # Use batch-based estimation if available
        if job.get('last_batch_duration') and job.get('current_batch'):
            completed_batches = job.get('current_batch', 1) - 1
            if completed_batches > 0:
                avg_batch_time = elapsed_time / completed_batches
                remaining_batches = job.get('total_batches', 0) - job.get('current_batch', 0)
                estimated_time_remaining = int(avg_batch_time * remaining_batches)
        else:
            # Fallback to item-based estimation
            items_per_second = processed / elapsed_time
            remaining_items = total - processed
            if items_per_second > 0:
                estimated_time_remaining = int(remaining_items / items_per_second)

    return {
        'job_id': job_id,
        'status': job.get('status'),
        'total': total,
        'processed': processed,
        'progress_percent': percent,
        'success_count': job.get('success_count', 0),
        'error_count': job.get('error_count', 0),
        'current_batch': job.get('current_batch', 0),
        'total_batches': job.get('total_batches', 0),
        'current_processing': job.get('current_processing'),
        'current_batch_items': job.get('current_batch_items', []),
        'last_batch_duration': job.get('last_batch_duration'),
        'batch_completed_at': job.get('batch_completed_at'),
        'estimated_time_remaining': estimated_time_remaining,
        'started_at': job.get('started_at'),
        'ended_at': job.get('ended_at'),
        'error': job.get('error')
    }


@router.get("/computers/warranty-debug")
def warranty_debug():
    """Debug endpoint to check computer data availability"""
    try:
        from ..managers.sql import sql_manager
        
        computers = sql_manager.get_computers_for_warranty_update()
        
        # Also get warranty data from database
        warranty_query = """
        SELECT 
            COUNT(*) as total_warranties,
            COUNT(CASE WHEN warranty_status = 'Active' THEN 1 END) as active_warranties,
            COUNT(CASE WHEN warranty_status = 'Expired' THEN 1 END) as expired_warranties,
            COUNT(CASE WHEN cache_expires_at < GETDATE() THEN 1 END) as needs_update
        FROM dell_warranty
        """
        warranty_stats = sql_manager.execute_query(warranty_query)
        
        # Sample of computers with service tags
        sample_with_tags = [c for c in computers[:10] if c.get('service_tag')]
        
        return {
            'warranty_eligible_count': len(computers),
            'warranty_eligible_sample': computers[:5],
            'computers_with_service_tags': len([c for c in computers if c.get('service_tag')]),
            'sample_with_service_tags': sample_with_tags,
            'warranty_statistics': warranty_stats[0] if warranty_stats else {},
            'total_computers_in_db': len(computers)
        }
    except Exception as e:
        return {'error': str(e)}


@router.get("/computers/warranty-jobs/active")
def get_active_warranty_jobs():
    """Get list of active warranty jobs"""
    try:
        active_jobs = []
        for job_id, job_data in _jobs.items():
            if job_data.get('status') in ['pending', 'running']:
                active_jobs.append({
                    'job_id': job_id,
                    'status': job_data.get('status'),
                    'started_at': job_data.get('started_at'),
                    'progress_percent': int((job_data.get('processed', 0) / job_data.get('total', 1)) * 100) if job_data.get('total', 0) > 0 else 0,
                    'processed': job_data.get('processed', 0),
                    'total': job_data.get('total', 0)
                })
        
        return {
            'active_jobs': active_jobs,
            'total_active': len(active_jobs)
        }
    except Exception as e:
        return {'error': str(e), 'active_jobs': []}
