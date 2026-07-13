import os
from typing import Optional

try:
    from pydantic_settings import BaseSettings
except ImportError:
    try:
        from pydantic import BaseSettings
    except ImportError:
        # Fallback to simple class
        class BaseSettings:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)

class Settings(BaseSettings):
    PROJECT_NAME: str = "VOLATRIA QUANT PLATFORM"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database configurations
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///volatria.db")
    
    # Security configurations
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super_secret_jwt_sign_key_for_institutional_volatria_platform")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # Logging & Observability
    LOG_LEVEL: str = "INFO"
    ENABLE_PROMETHEUS: bool = True

settings = Settings()
