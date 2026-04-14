import sys
import os
import importlib

# --- FIX PARA AMBIENTE DE SERVIÇO (NSSM) ---
# Garante que o Python encontre a pasta 'backend' e 'fastapi_app'
current_dir = os.path.dirname(os.path.abspath(__file__)) # pasta fastapi_app
parent_dir = os.path.dirname(current_dir)                # pasta backend
root_dir = os.path.dirname(parent_dir)                  # raiz do projeto

for path in [current_dir, parent_dir, root_dir]:
    if path not in sys.path:
        sys.path.append(path)
# -------------------------------------------

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .errors import register_exception_handlers
from .routes import computers_router, warranty_router, dhcp_router, sync_router, mobiles_router, iphone_catalog_router
from .routes.notifications import router as notifications_router
from .routes.warranty_jobs import router as warranty_jobs_router
from .routes.funcionarios import funcionarios_router
from .connections import test_all_connections
from .routes.debug_routes import debug_router

app = FastAPI(title="AD Inventory FastAPI",
              description="Backend para o sistema de inventário de computadores AD",
              version="0.1")

@app.get("/")
async def root():
    return {"message": "AD Inventory API is running", "status": "healthy"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_CREDENTIALS,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
    max_age=settings.CORS_MAX_AGE,
)

app.include_router(computers_router, prefix="/api/computers")
app.include_router(warranty_router, prefix="/api")
app.include_router(dhcp_router, prefix="/api/dhcp")
app.include_router(sync_router, prefix="/api")
app.include_router(notifications_router, prefix="/api")
app.include_router(warranty_jobs_router, prefix="/api")
app.include_router(funcionarios_router, prefix="/api/funcionarios")
app.include_router(debug_router, prefix="/api/debug")
app.include_router(mobiles_router, prefix="/api/mobiles")
app.include_router(iphone_catalog_router, prefix="/api/iphone-catalog")

register_exception_handlers(app)

@app.on_event("startup")
async def startup_event():
    # Removidos emojis para evitar UnicodeEncodeError no Windows Service
    print("FastAPI startup event")
    try:
        statuses = test_all_connections()
        print("Connection status summary:")
        for k, v in statuses.items():
            print(f" - {k}: {v}")
    except Exception as e:
        print(f"Error during connection tests at startup: {e}")

    try:
        # Tenta importar o módulo legacy
        mod = importlib.import_module('backend.app')

        from . import connections as _connections
        if getattr(mod, 'dhcp_manager', None) and getattr(_connections, 'dhcp_manager', None) is None:
            _connections.dhcp_manager = getattr(mod, 'dhcp_manager')
            print('Loaded dhcp_manager from backend.app')
            
        if getattr(mod, 'sync_service', None) and getattr(_connections, 'sync_service', None) is None:
            _connections.sync_service = getattr(mod, 'sync_service')
            print('Loaded sync_service from backend.app')
    except Exception as e:
        # Caractere 'i' comum no lugar do emoji para evitar erro de encoding
        print(f"(i) Could not import legacy backend.app managers: {e}")

    try:
        from .managers.user_detect_service import user_detect_scheduler
        user_detect_scheduler.start()
        print('UserDetectScheduler iniciado (seg-sex, 7h-19h, a cada 1h)')
    except Exception as e:
        print(f'Erro ao iniciar UserDetectScheduler: {e}')


@app.on_event("shutdown")
async def shutdown_event():
    print("FastAPI shutdown event")
    try:
        from .managers.user_detect_service import user_detect_scheduler
        user_detect_scheduler.stop()
    except Exception:
        pass


if __name__ == "__main__":
    import uvicorn
    # Mantendo a porta 42057 do seu .bat
    uvicorn.run("backend.fastapi_app.main:app", host="0.0.0.0", port=42057, reload=True)