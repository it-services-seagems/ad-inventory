import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    """Configurações da aplicação"""
    
    # Configurações do servidor
    HOST: str = Field(default="127.0.0.1", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # Configurações da API Dell
    DELL_CLIENT_ID: str = Field(..., env="DELL_CLIENT_ID")
    DELL_CLIENT_SECRET: str = Field(..., env="DELL_CLIENT_SECRET")
    DELL_BASE_URL: str = Field(default="https://apigtwb2c.us.dell.com", env="DELL_BASE_URL")
    
    # Configurações do banco de dados
    DATABASE_URL: str = Field(default="sqlite:///./warranties.db", env="DATABASE_URL")
    
    # Configurações do SQL Server (para consultas AD)
    SQL_SERVER_HOST: Optional[str] = Field(default=None, env="SQL_SERVER_HOST")
    SQL_SERVER_DATABASE: Optional[str] = Field(default=None, env="SQL_SERVER_DATABASE")
    SQL_SERVER_USERNAME: Optional[str] = Field(default=None, env="SQL_SERVER_USERNAME")
    SQL_SERVER_PASSWORD: Optional[str] = Field(default=None, env="SQL_SERVER_PASSWORD")
    SQL_SERVER_DRIVER: str = Field(default="ODBC Driver 17 for SQL Server", env="SQL_SERVER_DRIVER")
    
    # Configurações do Active Directory
    AD_SERVER: Optional[str] = Field(default=None, env="AD_SERVER")
    AD_USERNAME: Optional[str] = Field(default=None, env="AD_USERNAME")
    AD_PASSWORD: Optional[str] = Field(default=None, env="AD_PASSWORD")
    AD_DOMAIN: Optional[str] = Field(default=None, env="AD_DOMAIN")
    AD_BASE_DN: Optional[str] = Field(default=None, env="AD_BASE_DN")
    
    # Configurações de DHCP
    DHCP_SERVERS: dict = Field(default={
        "DIAMANTE": "10.15.1.1",
        "ESMERALDA": "10.15.2.1", 
        "JADE": "10.15.3.1",
        "RUBI": "10.15.4.1",
        "ONIX": "10.15.5.1",
        "TOPAZIO": "10.15.6.1",
        "SHQ": "10.15.0.1"
    }, env="DHCP_SERVERS")
    
    # Configurações de cache
    CACHE_TTL: int = Field(default=600, env="CACHE_TTL")  # 10 minutos
    
    # Configurações de segurança
    SECRET_KEY: str = Field(default="your-secret-key-change-in-production", env="SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Configurações de logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FILE: Optional[str] = Field(default=None, env="LOG_FILE")
    
    # Configurações de timeouts
    HTTP_TIMEOUT: int = Field(default=30, env="HTTP_TIMEOUT")
    DELL_API_TIMEOUT: int = Field(default=30, env="DELL_API_TIMEOUT")
    
    # Configurações de rate limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    def get_sql_server_connection_string(self) -> Optional[str]:
        """Gera string de conexão para SQL Server"""
        if not all([self.SQL_SERVER_HOST, self.SQL_SERVER_DATABASE, 
                   self.SQL_SERVER_USERNAME, self.SQL_SERVER_PASSWORD]):
            return None
            
        return (
            f"mssql+pyodbc://{self.SQL_SERVER_USERNAME}:{self.SQL_SERVER_PASSWORD}@"
            f"{self.SQL_SERVER_HOST}/{self.SQL_SERVER_DATABASE}?"
            f"driver={self.SQL_SERVER_DRIVER.replace(' ', '+')}&"
            f"TrustServerCertificate=yes"
        )

    @property
    def is_production(self) -> bool:
        """Verifica se está em produção"""
        return not self.DEBUG

    @property
    def cors_origins(self) -> list:
        """Retorna origens permitidas para CORS baseado no ambiente"""
        if self.DEBUG:
            return [
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:5000", 
                "http://127.0.0.1:5000"
            ]
        else:
            # Em produção, definir origens específicas
            return [
                "https://your-production-domain.com"
            ]

@lru_cache()
def get_settings() -> Settings:
    """Retorna instância singleton das configurações"""
    return Settings()