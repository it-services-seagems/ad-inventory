"""
Configuração centralizada de routers da API
"""
from typing import List, Dict, Any

# Configuração dos routers organizados por categoria
ROUTER_CONFIG: List[Dict[str, Any]] = [
    # Core system routers
    {
        "router": "computers_router",
        "prefix": "/api/computers",
        "tags": ["Computers"],
        "description": "Operações com computadores"
    },
    {
        "router": "funcionarios_router", 
        "prefix": "/api/funcionarios",
        "tags": ["Funcionários"],
        "description": "Gerenciamento de funcionários"
    },
    {
        "router": "users_router",
        "prefix": "/api/users", 
        "tags": ["Users"],
        "description": "Operações com usuários"
    },
    
    # Infrastructure routers
    {
        "router": "dhcp_router",
        "prefix": "/api/dhcp",
        "tags": ["DHCP"],
        "description": "Informações DHCP"
    },
    {
        "router": "winrm_router",
        "prefix": "/api/computers",
        "tags": ["WinRM"], 
        "description": "Operações WinRM"
    },
    
    # Service routers
    {
        "router": "warranty_router",
        "prefix": "/api",
        "tags": ["Warranty"],
        "description": "Garantias Dell"
    },
    {
        "router": "warranty_jobs_router",
        "prefix": "/api",
        "tags": ["Warranty Jobs"],
        "description": "Jobs de garantia"
    },
    {
        "router": "notifications_router",
        "prefix": "/api",
        "tags": ["Notifications"],
        "description": "Sistema de notificações"
    },
    {
        "router": "sync_router",
        "prefix": "/api",
        "tags": ["Sync"],
        "description": "Sincronização de dados"
    },
    
    # Debug & monitoring
    {
        "router": "debug_router",
        "prefix": "/api/debug",
        "tags": ["Debug"],
        "description": "Ferramentas de debug"
    }
]

# Tags para documentação OpenAPI
OPENAPI_TAGS = [
    {"name": "Health", "description": "Endpoints de saúde da API"},
    {"name": "Computers", "description": "Operações com computadores"},
    {"name": "Funcionários", "description": "Gerenciamento de funcionários"},
    {"name": "Users", "description": "Operações com usuários"},
    {"name": "DHCP", "description": "Informações DHCP"},
    {"name": "WinRM", "description": "Operações WinRM"},
    {"name": "Warranty", "description": "Garantias Dell"},
    {"name": "Warranty Jobs", "description": "Jobs de garantia"},
    {"name": "Notifications", "description": "Sistema de notificações"},
    {"name": "Sync", "description": "Sincronização de dados"},
    {"name": "Debug", "description": "Ferramentas de debug"},
]