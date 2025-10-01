from fastapi import APIRouter, HTTPException, Body, Query
from typing import Optional
import logging

from app.services.dhcp_manager import dhcp_manager

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get('/dhcp/filters/{organization}')
async def dhcp_filters(organization: str, service_tag: Optional[str] = Query(None), include_filters: bool = Query(False)):
    if not service_tag:
        raise HTTPException(status_code=400, detail='Parâmetro service_tag é obrigatório')

    try:
        result = dhcp_manager.search_filters_by_organization(organization, service_tag, include_filters)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.exception('Erro na rota dhcp/filters')
        # Maintain legacy behavior of returning 200 even on errors with debug info
        return {
            'ship_name': organization.upper(),
            'error': f'Erro ao consultar filtros DHCP: {str(e)}',
            'debug_info': {'organization': organization, 'service_tag': service_tag, 'error_details': str(e)},
            'timestamp': __import__('datetime').datetime.now().isoformat()
        }


@router.post('/dhcp/search')
async def dhcp_search(payload: dict = Body(...)):
    service_tag = payload.get('service_tag')
    ships = payload.get('ships')
    if not service_tag:
        raise HTTPException(status_code=400, detail='Campo "service_tag" é obrigatório no body')

    try:
        return dhcp_manager.search_post(service_tag, ships)
    except Exception:
        logger.exception('Erro na rota dhcp/search')
        return {'found': False, 'error': 'Erro interno ao buscar DHCP', 'service_tag': service_tag}


@router.get('/dhcp/test-connection')
async def dhcp_test_connection():
    try:
        return dhcp_manager.test_connections()
    except Exception:
        logger.exception('Erro em test-connection')
        return {'success': False, 'message': 'Erro ao testar conexões DHCP'}


@router.get('/dhcp/servers')
async def dhcp_servers():
    return dhcp_manager.get_servers_info()
