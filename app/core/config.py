from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    APP_NAME: str = "Gym Management API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/gymdb"

    JWT_SECRET_KEY: str = "your-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    SUPER_ADMIN_USERNAME: str = Field(
        default="admin",
        description="Initial super admin username. Set via SUPER_ADMIN_USERNAME env var.",
    )
    SUPER_ADMIN_PASSWORD: str = Field(
        default="admin",
        description="Initial super admin password. Set via SUPER_ADMIN_PASSWORD env var for security.",
    )
    REDIS_URL: str = "redis://localhost:6389/0"


settings = Settings()
