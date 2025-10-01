from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv

from app.config.settings import get_settings
from app.routers import dashboard, computer as computers, warranty, dhcp, service_tags

# Carregar variáveis de ambiente
load_dotenv()

# Criar aplicação FastAPI
app = FastAPI(
    title="Dell Warranty & Computer Management API",
    description="API para gerenciamento de computadores, garantias Dell e filtros DHCP",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*"
        # Adicionar seus domínios específicos aqui
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# Rota de teste
@app.get("/")
def root():
    return {
        "message": "Dell Warranty & Computer Management API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "status": "online"
    }

@app.get("/api")
def api_info():
    return {
        "message": "Dell Warranty API",
        "version": "1.0.0",
        "endpoints": {
            "dashboard": "/api/dashboard/*",
            "computers": "/api/computers/*",
            "warranty": "/api/warranty/*",
            "dhcp": "/api/dhcp/*",
            "service_tags": "/api/service-tag/*"
        }
    }

# Incluir rotas
app.include_router(dashboard.router, prefix="/api", tags=["Dashboard"])
app.include_router(warranty.router, prefix="/api/warranty", tags=["Warranty"])
app.include_router(computers.router, prefix="/api/computers", tags=["Computers"])
app.include_router(dhcp.router, prefix="/api", tags=["DHCP"])
app.include_router(service_tags.router, prefix="/api", tags=["Service Tags"])

# Handler de erro global
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return {
        "error": "Internal server error",
        "detail": str(exc),
        "path": str(request.url)
    }

if __name__ == '__main__':
    # Load settings only when starting the server directly (avoid import-time validation)
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info" if settings.DEBUG else "warning"
    )