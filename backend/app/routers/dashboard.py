from fastapi import APIRouter, HTTPException
from ..services.sql_manager import sql_manager
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get('/stats')
async def get_stats():
    try:
        total_q = "SELECT COUNT(*) as total FROM computers WHERE is_domain_controller = 0"
        recent_q = "SELECT COUNT(*) as recent FROM computers WHERE last_logon_timestamp > DATEADD(day, -7, GETDATE())"
        inactive_q = "SELECT COUNT(*) as inactive FROM computers WHERE last_logon_timestamp <= DATEADD(day, -30, GETDATE()) OR last_logon_timestamp IS NULL"

        total = 0
        recent = 0
        inactive = 0

        try:
            t = sql_manager.execute_query(total_q)
            total = int(t[0].get('total', 0)) if t else 0
        except Exception:
            logger.exception('Error fetching total')

        try:
            r = sql_manager.execute_query(recent_q)
            recent = int(r[0].get('recent', 0)) if r else 0
        except Exception:
            logger.exception('Error fetching recent')

        try:
            i = sql_manager.execute_query(inactive_q)
            inactive = int(i[0].get('inactive', 0)) if i else 0
        except Exception:
            logger.exception('Error fetching inactive')

        # Simple os distribution attempt
        os_dist = []
        try:
            os_q = "SELECT os as name, COUNT(*) as value FROM computers GROUP BY os"
            os_rows = sql_manager.execute_query(os_q)
            for r in os_rows:
                os_dist.append({'name': r.get('name') or 'Unknown', 'value': int(r.get('value') or 0)})
        except Exception:
            logger.exception('Error fetching os distribution')

        return {
            'totalComputers': total,
            'recentLogins': recent,
            'inactiveComputers': inactive,
            'osDistribution': os_dist
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
