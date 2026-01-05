from pydantic_settings import BaseSettings
from pydantic import ConfigDict

# Provide a sensible default DATABASE_URL so the application can start
# without requiring an environment variable during development/testing.
# For production, set the `DATABASE_URL` environment variable or `.env` file.
class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./iccs.db"
    REDIS_URL: str = "redis://localhost:6379"
    # Secret settings for JWT; set these in production via env or .env
    SECRET_KEY: str = "change-me-please"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    PRODUCT_DUPLICATE_THRESHOLD: float = 0.90
    OPENAI_API_KEY: str = ""

    model_config = ConfigDict(env_file=".env", extra="ignore")

settings = Settings()
