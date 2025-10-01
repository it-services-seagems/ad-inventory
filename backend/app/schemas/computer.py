from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class Computer(BaseModel):
    id: int
    name: str
    dns_hostname: Optional[str] = Field(None, alias="dnsHostName")
    distinguished_name: Optional[str] = Field(None, alias="dn")
    is_enabled: bool = Field(True, alias="isEnabled")
    description: Optional[str] = None
    last_logon_timestamp: Optional[datetime] = Field(None, alias="lastLogon")
    created_date: Optional[datetime] = Field(None, alias="created")
    organization_name: Optional[str] = Field(None, alias="organizationName")
    os: Optional[str] = None
    os_version: Optional[str] = Field(None, alias="osVersion")
    ip_address: Optional[str] = Field(None, alias="ipAddress")
    mac_address: Optional[str] = Field(None, alias="macAddress")

    class Config:
        populate_by_name = True
        from_attributes = True
