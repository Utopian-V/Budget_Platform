import secrets
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://budget_user:kWql5hpyWjR3lS0L4mHP55Sy1muhtUmx@dpg-d7encf77f7vs73bn89d0-a/budget_platform"
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    SECRET_KEY: str = secrets.token_urlsafe(32)
    FRONTEND_URL: str = "http://localhost:5173"
    ZOHO_CLIENT_ID: str = ""
    ZOHO_CLIENT_SECRET: str = ""
    ZOHO_ORG_ID: str = ""
    ZOHO_REFRESH_TOKEN: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
