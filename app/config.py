import os
from dotenv import load_dotenv
from app.path_utils import get_config_env_path

env_path = get_config_env_path()
if os.path.exists(env_path):
    load_dotenv(env_path, override=True)
else:
    load_dotenv(override=True)

class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "ECL Audit & Benchmarking Workbench")
    APP_ENV: str = os.getenv("APP_ENV", "development")
    APP_PORT: int = int(os.getenv("APP_PORT", "5154"))
    
    DB_TYPE: str = os.getenv("DB_TYPE", "sqlite") # sqlserver or sqlite
    DB_DRIVER: str = os.getenv("DB_DRIVER", "pymssql") # pymssql (no ODBC)
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_NAME: str = os.getenv("DB_NAME", "db_psak413_syariah")
    DB_USER: str = os.getenv("DB_USER", "sa")
    DB_PASS: str = os.getenv("DB_PASS", "Password123!")
    DB_PORT: str = os.getenv("DB_PORT", "1433")
    DB_FILE: str = os.getenv("DB_FILE", "db_psak413_syariah.db")

settings = Settings()
