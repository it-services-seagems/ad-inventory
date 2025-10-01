"""
Dell Warranty & Computer Management API

Sistema completo para gerenciamento de computadores, garantias Dell e filtros DHCP
usando FastAPI, SQLite e integração com Active Directory.
"""

__version__ = "1.0.0"
__author__ = "Your Team"
__description__ = "API para gerenciamento de computadores, garantias Dell e filtros DHCP"
__title__ = "Dell Warranty API"

# Metadados da aplicação
APP_METADATA = {
    "title": __title__,
    "description": __description__,
    "version": __version__,
    "author": __author__,
    "contact": {
        "name": "Suporte TI",
        "email": "suporte@empresa.com"
    },
    "license_info": {
        "name": "Internal Use Only",
    }
}

# Configurações padrão
DEFAULT_CONFIG = {
    "DATABASE_PATH": "warranties.db",
    "CACHE_TTL": 600,  # 10 minutos
    "LOG_LEVEL": "INFO",
    "API_PREFIX": "/api",
    "DOCS_URL": "/docs",
    "REDOC_URL": "/redoc"
}

def get_app_info():
    """Retorna informações da aplicação"""
    return {
        "name": __title__,
        "version": __version__,
        "description": __description__,
        "author": __author__
    }

def get_version():
    """Retorna versão da aplicação"""
    return __version__