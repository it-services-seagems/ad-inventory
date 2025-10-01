from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum

class WarrantyStatus(str, Enum):
    """Status da garantia"""
    ACTIVE = "active"
    EXPIRED = "expired"
    EXPIRING_30 = "expiring_30"  # Expirando em 30 dias
    EXPIRING_60 = "expiring_60"  # Expirando em 60 dias
    NO_DATA = "no_data"
    UNKNOWN = "unknown"

class EntitlementType(str, Enum):
    """Tipos de entitlement"""
    HARDWARE = "Hardware"
    SOFTWARE = "Software"
    SERVICE = "Service"

class WarrantyRequest(BaseModel):
    """Request para consulta de garantia"""
    service_tag: str = Field(..., min_length=5, max_length=20, description="Service tag Dell")

    @validator('service_tag')
    def validate_service_tag(cls, v):
        if v:
            return v.strip().upper()
        return v

class BulkWarrantyRequest(BaseModel):
    """Request para consulta em lote de garantias"""
    service_tags: List[str] = Field(..., min_items=1, max_items=50, description="Lista de service tags")
    max_workers: Optional[int] = Field(5, ge=1, le=10, description="Máximo de workers paralelos")
    delay_between_requests: Optional[float] = Field(0.5, ge=0.1, le=2.0, description="Delay entre requisições")

    @validator('service_tags')
    def validate_service_tags(cls, v):
        if v:
            return [tag.strip().upper() for tag in v if tag and tag.strip()]
        return v

class Entitlement(BaseModel):
    """Entitlement de garantia"""
    serviceLevelDescription: Optional[str] = Field(None, description="Descrição do nível de serviço")
    serviceLevelCode: Optional[str] = Field(None, description="Código do nível de serviço")
    startDate: Optional[str] = Field(None, description="Data de início (ISO string)")
    endDate: Optional[str] = Field(None, description="Data de fim (ISO string)")
    entitlementType: Optional[str] = Field(None, description="Tipo de entitlement")
    itemNumber: Optional[str] = Field(None, description="Número do item")

class WarrantyInfo(BaseModel):
    """Informações de garantia Dell"""
    serviceTag: str = Field(..., description="Service tag original")
    serviceTagLimpo: Optional[str] = Field(None, description="Service tag sem prefixos")
    modelo: Optional[str] = Field(None, description="Modelo do equipamento")
    productLineDescription: Optional[str] = Field(None, description="Descrição da linha de produto")
    systemDescription: Optional[str] = Field(None, description="Descrição do sistema")
    dataExpiracao: Optional[str] = Field(None, description="Data de expiração (formato brasileiro)")
    warrantyEndDate: Optional[str] = Field(None, description="Data de fim da garantia (ISO)")
    status: Optional[str] = Field(None, description="Status da garantia")
    warrantyStatus: Optional[str] = Field(None, description="Status da garantia (formato Dell)")
    entitlements: List[Entitlement] = Field(default_factory=list, description="Lista de entitlements")
    shipDate: Optional[str] = Field(None, description="Data de envio")
    orderNumber: Optional[str] = Field(None, description="Número do pedido")
    dataSource: Optional[str] = Field(None, description="Fonte dos dados")
    response_time_ms: Optional[int] = Field(None, description="Tempo de resposta em ms")

class WarrantyError(BaseModel):
    """Erro na consulta de garantia"""
    error: str = Field(..., description="Mensagem de erro")
    code: str = Field(..., description="Código do erro")
    serviceTag: Optional[str] = Field(None, description="Service tag que causou o erro")

class WarrantyResponse(BaseModel):
    """Resposta da consulta de garantia (pode ser sucesso ou erro)"""
    __root__: Union[WarrantyInfo, WarrantyError]

class BulkWarrantyResult(BaseModel):
    """Resultado individual do processamento em lote"""
    service_tag: str = Field(..., description="Service tag processado")
    success: bool = Field(..., description="Se foi processado com sucesso")
    modelo: Optional[str] = Field(None, description="Modelo se sucesso")
    status: Optional[str] = Field(None, description="Status se sucesso")
    data_expiracao: Optional[str] = Field(None, description="Data de expiração se sucesso")
    response_time: Optional[int] = Field(None, description="Tempo de resposta em ms")
    error: Optional[str] = Field(None, description="Mensagem de erro se falha")
    code: Optional[str] = Field(None, description="Código de erro se falha")

class BulkWarrantyResponse(BaseModel):
    """Resposta do processamento em lote"""
    total: int = Field(..., description="Total processado")
    success: int = Field(..., description="Sucessos")
    errors: int = Field(..., description="Erros")
    skipped: int = Field(..., description="Pulados")
    start_time: datetime = Field(..., description="Hora de início")
    end_time: Optional[datetime] = Field(None, description="Hora de fim")
    duration: Optional[float] = Field(None, description="Duração em segundos")
    details: List[BulkWarrantyResult] = Field(default_factory=list, description="Detalhes por service tag")

class TokenStatus(BaseModel):
    """Status do token Dell"""
    token_valid: bool = Field(..., description="Se o token está válido")
    expires_at: Optional[str] = Field(None, description="Quando expira (ISO string)")
    has_token: bool = Field(..., description="Se possui token")

class TokenRefresh(BaseModel):
    """Resposta da renovação do token"""
    message: str = Field(..., description="Mensagem de resultado")
    expires_at: Optional[str] = Field(None, description="Nova data de expiração")

class HealthCheck(BaseModel):
    """Status de saúde da API Dell"""
    status: str = Field(..., description="Status da API (healthy/unhealthy)")
    dell_api_accessible: bool = Field(..., description="Se a API Dell está acessível")
    timestamp: float = Field(..., description="Timestamp da verificação")
    error: Optional[str] = Field(None, description="Erro se houver")

class WarrantySummaryItem(BaseModel):
    """Item do resumo de garantias"""
    computer_id: int = Field(..., description="ID do computador")
    computer_name: str = Field(..., description="Nome do computador")
    service_tag: Optional[str] = Field(None, description="Service tag")
    warranty_status: Optional[str] = Field(None, description="Status da garantia")
    warranty_end_date: Optional[str] = Field(None, description="Data de fim da garantia")
    model: Optional[str] = Field(None, description="Modelo")
    last_checked: Optional[datetime] = Field(None, description="Última verificação")
    last_error: Optional[str] = Field(None, description="Último erro se houver")

class WarrantySummaryResponse(BaseModel):
    """Resposta do resumo de garantias"""
    warranties: List[WarrantySummaryItem] = Field(..., description="Lista de garantias")
    total: int = Field(..., description="Total de registros")
    summary: Dict[str, int] = Field(..., description="Resumo por status")
    last_updated: Optional[datetime] = Field(None, description="Última atualização")

class WarrantyStatusInfo(BaseModel):
    """Informações de status da garantia para UI"""
    status: str = Field(..., description="Status interno")
    text: str = Field(..., description="Texto para exibição")
    color: str = Field(..., description="Classe CSS de cor")
    bgColor: str = Field(..., description="Classe CSS de background")
    icon: str = Field(..., description="Nome do ícone")
    sortValue: int = Field(..., description="Valor para ordenação")

# Funções auxiliares para conversão
def warranty_status_to_info(warranty_data: Optional[Dict[str, Any]]) -> WarrantyStatusInfo:
    """Converte dados de garantia em informações de status para UI"""
    if not warranty_data or warranty_data.get('last_error'):
        return WarrantyStatusInfo(
            status="unknown",
            text="Desconhecido",
            color="text-gray-500",
            bgColor="bg-gray-100",
            icon="Shield",
            sortValue=999999
        )

    if not warranty_data.get('warranty_end_date'):
        return WarrantyStatusInfo(
            status="no_data",
            text="Sem dados",
            color="text-gray-500",
            bgColor="bg-gray-100",
            icon="Shield",
            sortValue=999998
        )

    try:
        end_date = datetime.fromisoformat(warranty_data['warranty_end_date'].replace('Z', '+00:00'))
        now = datetime.now(end_date.tzinfo)
        diff_days = (end_date - now).days

        if diff_days < 0:
            return WarrantyStatusInfo(
                status="expired",
                text=f"Expirada há {abs(diff_days)} dias",
                color="text-red-600",
                bgColor="bg-red-100",
                icon="ShieldX",
                sortValue=diff_days
            )
        elif diff_days <= 30:
            return WarrantyStatusInfo(
                status="expiring_30",
                text=f"Expira em {diff_days} dias",
                color="text-orange-600",
                bgColor="bg-orange-100",
                icon="ShieldAlert",
                sortValue=diff_days
            )
        elif diff_days <= 60:
            return WarrantyStatusInfo(
                status="expiring_60",
                text=f"Expira em {diff_days} dias",
                color="text-yellow-600",
                bgColor="bg-yellow-100",
                icon="ShieldAlert",
                sortValue=diff_days
            )
        else:
            return WarrantyStatusInfo(
                status="active",
                text=f"Ativa ({diff_days} dias)",
                color="text-green-600",
                bgColor="bg-green-100",
                icon="ShieldCheck",
                sortValue=diff_days
            )
    except:
        return WarrantyStatusInfo(
            status="unknown",
            text="Erro na data",
            color="text-gray-500",
            bgColor="bg-gray-100",
            icon="Shield",
            sortValue=999997
        )