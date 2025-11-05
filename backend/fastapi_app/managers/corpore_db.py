import os
import logging
import importlib.util
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Load dotenv if available
if importlib.util.find_spec('dotenv') is not None:
    try:
        from dotenv import load_dotenv
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        env_path = os.path.join(base_dir, '.env')
        if os.path.exists(env_path):
            load_dotenv(env_path)
    except Exception:
        pass


class DatabaseConfig:
    """Helpers para abrir conexões com os bancos usados pelo app."""

    # CorporeRM (SQL Server via pyodbc)
    CORPORE_DRIVER = os.getenv('CORPORE_DRIVER', 'SQL Server')
    CORPORE_SERVER = os.getenv('CORPORE_SERVER', 'closql01')
    CORPORE_DATABASE = os.getenv('CORPORE_DATABASE', 'CorporeRM')
    CORPORE_UID = os.getenv('CORPORE_UID', 'powerbi')
    CORPORE_PWD = os.getenv('CORPORE_PWD', 'PWRBI@SE@GEM$')
    CORPORE_TRUSTED_CONNECTION = os.getenv('CORPORE_TRUSTED_CONNECTION', 'no')
    CORPORE_TIMEOUT = os.getenv('CORPORE_TIMEOUT', '30')

    # registry for named queries
    queries: Dict[str, str] = {}

    @classmethod
    def set_query(cls, name: str, sql: str) -> None:
        cls.queries[name] = sql

    @classmethod
    def get_query(cls, name: str) -> Optional[str]:
        return cls.queries.get(name)

    @classmethod
    def _corp_odbc_str(cls) -> str:
        return (
            f"DRIVER={{{cls.CORPORE_DRIVER}}};"
            f"SERVER={cls.CORPORE_SERVER};"
            f"DATABASE={cls.CORPORE_DATABASE};"
            f"UID={cls.CORPORE_UID};"
            f"PWD={cls.CORPORE_PWD};"
            f"Connection Timeout={cls.CORPORE_TIMEOUT};"
        )

    @classmethod
    def get_pyodbc_connection_string(cls, which: str = 'corporerm') -> str:
        """Return a pyodbc connection string for the requested DB."""
        return cls._corp_odbc_str()

    @classmethod
    def get_pyodbc_connection(cls, which: str = 'corporerm'):
        """Return an open pyodbc connection. Caller is responsible for closing it."""
        try:
            import pyodbc
        except Exception as e:
            raise RuntimeError('pyodbc is required for SQL Server connections') from e

        conn_str = cls.get_pyodbc_connection_string(which)
        return pyodbc.connect(conn_str)