from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class ComputerSource(str, Enum):
    """Fonte dos dados do computador"""
    SQL = "sql"
    AD = "ad"
    CACHE = "cache"

class ComputerStatus(str, Enum):
    """Status do computador"""
    ENABLED = "enabled"
    DISABLED = "disabled"
    ALL = "all"

class LoginStatus(str, Enum):
    """Status de login"""
    RECENT = "recent"      # 7 dias
    MODERATE = "moderate"  # 8-30 dias  
    OLD = "old"           # 30+ dias
    NEVER = "never"       # Nunca logou
    ALL = "all"

class OU(BaseModel):
    """Unidade Organizacional"""
    code: str = Field(..., description="Código da OU (ex: DIA, ESM)")
    name: str = Field(..., description="Nome da OU (ex: Diamante, Esmeralda)")
    color: str = Field(..., description="Classe CSS de cor")
    bgColor: str = Field(..., description="Classe CSS de background")
    count: Optional[int] = Field(None, description="Quantidade de computadores nesta OU")

class LoginStatusInfo(BaseModel):
    """Informações de status de login"""
    status: str = Field(..., description="Status do login")
    color: str = Field(..., description="Classe CSS de cor")
    text: str = Field(..., description="Texto para exibição")
    bgColor: str = Field(..., description="Classe CSS de background")
    sortValue: int = Field(..., description="Valor para ordenação")

class Computer(BaseModel):
    """Modelo base do computador"""
    id: Optional[int] = Field(None, description="ID único do computador")
    name: str = Field(..., description="Nome do computador", min_length=1)
    service_tag: Optional[str] = Field(None, description="Service tag Dell")
    os: Optional[str] = Field(None, description="Sistema operacional")
    os_version: Optional[str] = Field(None, alias="osVersion", description="Versão do SO")
    description: Optional[str] = Field(None, description="Descrição do computador")
    dns_hostname: Optional[str] = Field(None, alias="dnsHostName", description="DNS hostname")
    distinguished_name: Optional[str] = Field(None, alias="dn", description="Distinguished Name")
    last_logon: Optional[datetime] = Field(None, alias="lastLogon", description="Último login")
    created_date: Optional[datetime] = Field(None, alias="created", description="Data de criação")
    disabled: bool = Field(False, description="Se o computador está desabilitado")
    user_account_control: Optional[int] = Field(None, alias="userAccountControl", description="User Account Control")
    primary_group_id: Optional[int] = Field(None, alias="primaryGroupID", description="Primary Group ID")
    
    # Campos calculados (não vêm do banco)
    isEnabled: Optional[bool] = Field(None, description="Se está habilitado (calculado)")
    loginStatus: Optional[LoginStatusInfo] = Field(None, description="Status de login (calculado)")
    ou: Optional[OU] = Field(None, description="Unidade Organizacional (calculado)")
    
    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

class ComputerDetail(Computer):
    """Modelo detalhado do computador com informações extras"""
    warranty: Optional[Dict[str, Any]] = Field(None, description="Informações de garantia")
    dhcp_info: Optional[Dict[str, Any]] = Field(None, description="Informações DHCP")
    last_user_info: Optional[Dict[str, Any]] = Field(None, description="Informações do último usuário")

class ComputerFilters(BaseModel):
    """Filtros para listagem de computadores"""
    status: ComputerStatus = Field(ComputerStatus.ALL, description="Filtro por status")
    os: str = Field("all", description="Filtro por sistema operacional")
    lastLogin: LoginStatus = Field(LoginStatus.ALL, description="Filtro por último login")
    ou: str = Field("all", description="Filtro por OU")
    warranty: str = Field("all", description="Filtro por status de garantia")
    source: ComputerSource = Field(ComputerSource.SQL, description="Fonte dos dados")

class ComputerQuery(BaseModel):
    """Parâmetros de consulta para computadores"""
    source: Optional[ComputerSource] = Field(ComputerSource.SQL, description="Fonte dos dados")
    limit: Optional[int] = Field(None, ge=1, le=1000, description="Limite de resultados")
    offset: Optional[int] = Field(0, ge=0, description="Offset para paginação")
    search: Optional[str] = Field(None, min_length=1, description="Termo de busca")
    filters: Optional[ComputerFilters] = Field(None, description="Filtros avançados")

class ComputerStats(BaseModel):
    """Estatísticas dos computadores"""
    total: int = Field(..., description="Total de computadores")
    enabled: int = Field(..., description="Computadores habilitados")
    disabled: int = Field(..., description="Computadores desabilitados")
    recent: int = Field(..., description="Com login recente (7 dias)")
    old: int = Field(..., description="Inativos (30+ dias)")
    never: int = Field(..., description="Nunca fizeram login")
    warrantyActive: int = Field(0, description="Garantias ativas")
    warrantyExpired: int = Field(0, description="Garantias expiradas")
    warrantyExpiring30: int = Field(0, description="Expirando em 30 dias")
    warrantyExpiring60: int = Field(0, description="Expirando em 60 dias")
    warrantyUnknown: int = Field(0, description="Garantias desconhecidas")
    byOU: Dict[str, Any] = Field(default_factory=dict, description="Estatísticas por OU")

class ComputerResponse(BaseModel):
    """Resposta da listagem de computadores"""
    computers: List[Computer] = Field(..., description="Lista de computadores")
    total: int = Field(..., description="Total de registros")
    stats: ComputerStats = Field(..., description="Estatísticas")
    uniqueOSList: List[str] = Field(..., description="Lista única de SOs")
    uniqueOUList: List[OU] = Field(..., description="Lista única de OUs")
    isFromCache: bool = Field(False, description="Se os dados vieram do cache")
    lastFetchTime: Optional[datetime] = Field(None, description="Hora da última busca")

class SyncResult(BaseModel):
    """Resultado de sincronização"""
    success: bool = Field(..., description="Se a sincronização foi bem sucedida")
    message: str = Field(..., description="Mensagem de resultado")
    stats: Optional[Dict[str, Any]] = Field(None, description="Estatísticas da sincronização")

class LastUserLogon(BaseModel):
    """Informações de logon do usuário"""
    user: str = Field(..., description="Nome do usuário")
    time: datetime = Field(..., description="Horário do logon")
    logon_type: str = Field(..., description="Tipo de logon")
    source_ip: Optional[str] = Field(None, description="IP de origem")
    logon_process: Optional[str] = Field(None, description="Processo de logon")

class LastUserInfo(BaseModel):
    """Informações do último usuário"""
    success: bool = Field(..., description="Se a consulta foi bem sucedida")
    computer_name: str = Field(..., description="Nome do computador")
    service_tag: Optional[str] = Field(None, description="Service tag")
    last_user: Optional[str] = Field(None, description="Último usuário")
    last_logon_time: Optional[datetime] = Field(None, description="Horário do último logon")
    logon_type: Optional[str] = Field(None, description="Tipo de logon")
    search_method: str = Field(..., description="Método de busca utilizado")
    connection_method: Optional[str] = Field(None, description="Método de conexão")
    computer_found: bool = Field(False, description="Se o computador foi encontrado")
    recent_logons: List[LastUserLogon] = Field(default_factory=list, description="Logons recentes")
    total_time: Optional[float] = Field(None, description="Tempo total da consulta")
    error: Optional[str] = Field(None, description="Mensagem de erro se houver")

# Validadores personalizados
@validator('name', pre=True, always=True)
def validate_computer_name(cls, v):
    if v:
        return v.strip().upper()
    return v

Computer.update_forward_refs()
ComputerDetail.update_forward_refs()