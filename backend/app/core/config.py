"""
Application Configuration
"""
import json
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Union


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:1234@localhost:5432/Bugbust3r"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Docker
    DOCKER_SOCKET: str = "unix://var/run/docker.sock"
    
    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production-use-env-variable"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS (accept JSON string from docker-compose env)
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, list]) -> list:
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [o.strip() for o in v.split(",") if o.strip()]
        return v
    
    # Application
    PROJECT_NAME: str = "Security Scanner"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"  # Allow extra fields from environment


settings = Settings()


