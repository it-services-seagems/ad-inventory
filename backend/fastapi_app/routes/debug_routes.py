from fastapi import APIRouter
from ..connections import test_all_connections

debug_router = APIRouter()


@debug_router.get('/connections')
def debug_connections():
    """Return a summary of connection availability for SQL, DHCP, Dell API, etc."""
    try:
        return test_all_connections()
    except Exception as e:
        return {'error': str(e)}
