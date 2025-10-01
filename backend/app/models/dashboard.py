from pydantic import BaseModel, Field
from typing import List, Dict, Any
from datetime import datetime

class OSDistribution(BaseModel):
    """Distribuição por sistema operacional"""
    name: str = Field(..., description="Nome do sistema operacional")
    value: int = Field(..., description="Quantidade de máquinas")

class DashboardStats(BaseModel):
    """Estatísticas do dashboard"""
    totalComputers: int = Field(..., description="Total de computadores")
    recentLogins: int = Field(..., description="Logins recentes (7 dias)")
    inactiveComputers: int = Field(..., description="Computadores inativos (30+ dias)")
    neverLoggedIn: int = Field(0, description="Nunca fizeram login")
    enabledComputers: int = Field(0, description="Computadores habilitados")
    disabledComputers: int = Field(0, description="Computadores desabilitados")
    
    # Garantias
    warrantyActive: int = Field(0, description="Garantias ativas")
    warrantyExpired: int = Field(0, description="Garantias expiradas")
    warrantyExpiring30: int = Field(0, description="Expirando em 30 dias")
    warrantyExpiring60: int = Field(0, description="Expirando em 60 dias")
    warrantyUnknown: int = Field(0, description="Garantias desconhecidas")
    
    # Distribuições
    osDistribution: List[OSDistribution] = Field(default_factory=list, description="Distribuição por SO")
    ouDistribution: List[Dict[str, Any]] = Field(default_factory=list, description="Distribuição por OU")
    
    # Metadados
    lastUpdated: datetime = Field(default_factory=datetime.now, description="Última atualização")
    dataSource: str = Field("sql", description="Fonte dos dados")
    cacheExpires: datetime = Field(default_factory=datetime.now, description="Cache expira em")