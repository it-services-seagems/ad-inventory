from fastapi import FastAPI, BackgroundTasks, HTTPException
import threading
import time
import uuid
from typing import Optional

app = FastAPI(title="Warranty Worker Only", version="0.1")

# Simple in-memory job store
_jobs = {}


def _chunk_list(seq, size=100):
    for i in range(0, len(seq), size):
        yield seq[i:i + size]


def _convert_raw_to_processed(raw, service_tag):
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
        processed = {
            'success': True,
            'service_tag': service_tag,
            'service_tag_clean': service_tag,
            'warranty_start_date': warranty_start_date,
            'warranty_end_date': warranty_end_date,
            'warranty_status': warranty_status,
            'product_line_description': raw.get('productLineDescription') if raw else '',
            'system_description': raw.get('systemDescription') if raw else '',
            'ship_date': raw.get('shipDate') if raw else None,
            'order_number': raw.get('orderNumber') if raw else None,
            'entitlements': None,
            'last_updated': None,
            'cache_expires_at': None,
            'last_error': None
        }
        try:
            import json
            processed['entitlements'] = json.dumps(entitlements, default=str)
        except Exception:
            processed['entitlements'] = None
        from datetime import datetime, timedelta
        processed['last_updated'] = datetime.now()
        processed['cache_expires_at'] = datetime.now() + timedelta(days=7)
        return processed
    except Exception as e:
        return {'success': False, 'error': str(e), 'code': 'PROCESS_ERROR', 'service_tag': service_tag}


@app.post('/api/computers/warranty-refresh')
def start_warranty_refresh(background_tasks: BackgroundTasks, mode: Optional[str] = 'full'):
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {'id': job_id, 'status': 'pending', 'total': 0, 'processed': 0, 'started_at': None, 'ended_at': None, 'error': None}

    def _runner(jid: str):
        try:
            _jobs[jid]['status'] = 'running'
            _jobs[jid]['started_at'] = time.time()

            # lazy import legacy script to avoid heavy imports at module load
            from backend import debug_c1wsb92 as legacy

            updater = legacy.DellWarrantyBulkUpdater()
            updater.request_delay = 2

            computers = updater.get_computers_to_process()
            tags = [c['service_tag'] for c in computers if c.get('service_tag')]
            tag_to_id = {c['service_tag']: c['id'] for c in computers if c.get('service_tag')}
            batches = list(_chunk_list(tags, 100))
            _jobs[jid]['total'] = len(tags)

            checker = legacy.DellWarrantyChecker(servicetags_list=[], client_id=None, client_secret=None, max_workers=1, batch_size=100, request_delay=2)

            processed_count = 0
            for batch in batches:
                results = checker.process_warranty_batch(batch)
                for raw in results:
                    service_tag = None
                    if isinstance(raw, dict):
                        service_tag = raw.get('serviceTag') or raw.get('service_tag') or raw.get('servicetag')
                    if not service_tag and isinstance(raw, dict):
                        service_tag = raw.get('serviceTag') if raw.get('serviceTag') else None
                    if not service_tag:
                        processed_count += 1
                        _jobs[jid]['processed'] = processed_count
                        continue
                    processed = _convert_raw_to_processed(raw, service_tag)
                    computer_id = tag_to_id.get(service_tag)
                    if computer_id:
                        try:
                            updater.save_warranty_to_database(computer_id, processed)
                        except Exception:
                            pass
                    processed_count += 1
                    _jobs[jid]['processed'] = processed_count
                time.sleep(2)

            _jobs[jid]['status'] = 'completed'
            _jobs[jid]['ended_at'] = time.time()
        except Exception as e:
            _jobs[jid]['status'] = 'failed'
            _jobs[jid]['error'] = str(e)
            _jobs[jid]['ended_at'] = time.time()

    thread = threading.Thread(target=_runner, args=(job_id,), daemon=True)
    thread.start()

    return {'job_id': job_id}


@app.get('/api/computers/warranty-refresh/{job_id}')
def warranty_refresh_status(job_id: str):
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail='Job not found')
    total = job.get('total') or 0
    processed = job.get('processed') or 0
    percent = int((processed / total) * 100) if total > 0 else (100 if job.get('status') == 'completed' else 0)
    return {'job_id': job_id, 'status': job.get('status'), 'total': total, 'processed': processed, 'progress_percent': percent, 'error': job.get('error')}


if __name__ == '__main__':
    import uvicorn
    uvicorn.run('backend.warranty_worker_only:app', host='0.0.0.0', port=42061, reload=False)
