from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .errors import register_exception_handlers
from .routes import computers_router, warranty_router, dhcp_router, sync_router
from .routes.notifications import router as notifications_router
from .routes.warranty_jobs import router as warranty_jobs_router
from .routes.funcionarios import funcionarios_router
from .connections import test_all_connections
from .routes.debug_routes import debug_router

app = FastAPI(title="AD Inventory FastAPI",
              description="Backend para o sistema de inventário de computadores AD  ",
              version="0.1")

# CORS - mirror the permissive dev settings used previously
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_CREDENTIALS,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
    max_age=settings.CORS_MAX_AGE,
)

# Register routers
app.include_router(computers_router, prefix="/api/computers")
app.include_router(warranty_router, prefix="/api")
app.include_router(dhcp_router, prefix="/api/dhcp")
app.include_router(sync_router, prefix="/api")
app.include_router(notifications_router, prefix="/api")
app.include_router(warranty_jobs_router, prefix="/api")
app.include_router(funcionarios_router, prefix="/api/funcionarios")
app.include_router(debug_router, prefix="/api/debug")

# Register error handlers
register_exception_handlers(app)


@app.on_event("startup")
async def startup_event():
    # Placeholder for any startup tasks (connections, warmups)
    print("🚀 FastAPI startup event")
    try:
        statuses = test_all_connections()
        print("🔌 Connection status summary:")
        for k, v in statuses.items():
            print(f" - {k}: {v}")
    except Exception as e:
        print(f"⚠️ Error during connection tests at startup: {e}")

    # Try to import legacy backend.app to reuse its managers (dhcp_manager, sync_service)
    try:
        import importlib
        mod = importlib.import_module('backend.app')

        # populate connections module so require_dhcp_manager / require_sync_service succeed
        from . import connections as _connections
        if getattr(mod, 'dhcp_manager', None) and getattr(_connections, 'dhcp_manager', None) is None:
            _connections.dhcp_manager = getattr(mod, 'dhcp_manager')
            print('🔁 Loaded dhcp_manager from backend.app')
        if getattr(mod, 'sync_service', None) and getattr(_connections, 'sync_service', None) is None:
            _connections.sync_service = getattr(mod, 'sync_service')
            print('🔁 Loaded sync_service from backend.app')
    except Exception as e:
        # don't fail startup; log reason for easier debugging
        print(f"ℹ️ Could not import legacy backend.app managers: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    print(" FastAPI shutdown event")


if __name__ == "__main__":
    import uvicorn
    # Use fully-qualified module path so running from repository root works
    uvicorn.run("backend.fastapi_app.main:app", host="0.0.0.0", port=42059, reload=True)
