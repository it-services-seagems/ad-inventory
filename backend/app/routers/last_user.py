from fastapi import APIRouter, HTTPException, Query
from ..services.ad_eventlog import ADEventLogLastUserService
from ..services.ad_manager import ad_manager
from ..core.config import settings

router = APIRouter()

# Instantiate service with credentials from settings
ad_eventlog_service = ADEventLogLastUserService(
    usuario=settings.AD_USERNAME,
    senha=settings.AD_PASSWORD
)


@router.get('/computers/{computer_name}/last-user')
async def get_last_user_by_computer(computer_name: str, days: int = Query(30)):
    # Resolve DC from settings
    dc = settings.AD_SERVER.replace('ldap://', '').replace('ldaps://', '') if settings.AD_SERVER else None
    result = ad_eventlog_service.buscar_ultimo_logon_por_computador(computer_name, dias_historico=days, dc_name=dc)
    # Always return 200 with details (compat with frontend)
    return result


@router.get('/service-tag/{service_tag}/last-user')
async def get_last_user_by_service_tag(service_tag: str, days: int = Query(30)):
    dc = settings.AD_SERVER.replace('ldap://', '').replace('ldaps://', '') if settings.AD_SERVER else None
    result = ad_eventlog_service.buscar_logon_por_service_tag_via_ad(service_tag, dias_historico=days, ad_manager=ad_manager, dc_name=dc)
    return result


@router.get('/last-user/test-dc-connection')
async def test_dc_connection():
    dc = settings.AD_SERVER.replace('ldap://', '').replace('ldaps://', '') if settings.AD_SERVER else None
    client = ad_eventlog_service.conectar_domain_controller(dc) if dc else None
    if client:
        return {'success': True, 'domain_controller': dc}
    return {'success': False, 'domain_controller': dc, 'error': 'Unable to connect'}


@router.get('/last-user/search-events-sample')
async def search_events_sample(days: int = Query(1), max_events: int = Query(50)):
    dc = settings.AD_SERVER.replace('ldap://', '').replace('ldaps://', '') if settings.AD_SERVER else None
    if not dc:
        raise HTTPException(status_code=400, detail='Domain controller not configured')
    # For now, reuse buscar_ultimo_logon_por_computador with a placeholder computer name to collect sample
    # The detailed sample implementation can be added later
    sample = {'success': False, 'message': 'Sample search not fully implemented in migration', 'domain_controller': dc}
    return sample


@router.get('/last-user/debug-ad-eventlog/{computer_name}')
async def debug_ad_eventlog(computer_name: str):
    dc = settings.AD_SERVER.replace('ldap://', '').replace('ldaps://', '') if settings.AD_SERVER else None
    debug_info = {
        'computer_name': computer_name,
        'domain_controller': dc,
        'tests': {}
    }
    # DC connectivity
    client = ad_eventlog_service.conectar_domain_controller(dc) if dc else None
    debug_info['tests']['dc_connectivity'] = {'connected': bool(client), 'dc': dc}
    # AD lookup
    try:
        found = None
        if ad_manager.connect():
            found = ad_manager.find_computer(computer_name)
            ad_manager.connection.unbind()
        debug_info['tests']['ad_lookup'] = {'found': bool(found), 'computer': found}
    except Exception as e:
        debug_info['tests']['ad_lookup'] = {'error': str(e)}

    # Run event search if DC ok
    if client:
        events = ad_eventlog_service.buscar_ultimo_logon_por_computador(computer_name, dc_name=dc)
        debug_info['tests']['dc_event_search'] = events
    else:
        debug_info['tests']['dc_event_search'] = {'skipped': True}

    return debug_info
