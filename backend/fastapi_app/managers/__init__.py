"""Expose manager singletons for FastAPI migration.

Modules:
- sql: SQLManager -> sql_manager
- ad: ADManager -> ad_manager
- ad_computer: ADComputerManager -> ad_computer_manager

Import these from routers to use the new implementations instead of pulling from the old Flask app.
"""
from .sql import sql_manager
from .ad import ad_manager
from .ad_computer import ad_computer_manager
from .dhcp import dhcp_manager
from .sync_service import sync_service

__all__ = ["sql_manager", "ad_manager", "ad_computer_manager", "dhcp_manager", "sync_service"]
