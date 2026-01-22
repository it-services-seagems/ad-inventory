from .computers import computers_router
from .warranty import warranty_router
from .dhcp import dhcp_router
from .sync import sync_router
from .mobiles import mobiles_router
from .iphone_catalog import router as iphone_catalog_router

__all__ = [
    'computers_router',
    'warranty_router',
    'dhcp_router',
    'sync_router',
    'mobiles_router',
    'iphone_catalog_router',
]
