import secrets
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://neondb_owner:npg_f3SKZXPQvF0N@ep-dawn-recipe-a1bd62ap.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"
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
