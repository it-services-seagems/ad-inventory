from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from ..connections import require_dhcp_manager

dhcp_router = APIRouter()


@dhcp_router.get('/servers')
def get_servers():
    try:
        dhcp = require_dhcp_manager()
        return JSONResponse(content={
            'servers': dhcp.all_servers,
            'organization_mapping': dhcp.org_to_servers,
            'prefix_mapping': dhcp.prefix_to_org,
            'supported_prefixes': dhcp.prefixos,
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@dhcp_router.get('/filters/{ship_name}')
def get_dhcp_filters_by_ship(ship_name: str, service_tag: str = None, include_filters: bool = True):
    """Get DHCP filters for a specific ship/organization"""
    try:
        dhcp = require_dhcp_manager()
        
        # This route currently returns 404 as the full implementation is not ready
        # The /search route should be used instead for now
        raise HTTPException(
            status_code=404, 
            detail=f"DHCP filters endpoint for {ship_name} not implemented. Use /dhcp/search instead."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@dhcp_router.post('/search')
def search(payload: dict):
    try:
        tag = payload.get('service_tag')
        ships = payload.get('ships') or []
        dhcp = require_dhcp_manager()
        # Use the first server in ships mapping or all servers
        servers = []
        for ship in ships:
            org = dhcp.get_organization_from_prefix(ship)
            servers += dhcp.org_to_servers.get(org, [])
        if not servers:
            servers = dhcp.all_servers

        results = []
        for s in servers:
            res = dhcp.buscar_service_tag_servidor(s, tag)
            results.append(res)

        return JSONResponse(content={'results': results})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
