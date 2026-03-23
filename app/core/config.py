from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env")

    DATABASE_URL: str
    APP_NAME: str = "BlaBlaGoa"
    DEBUG: bool = False
    SECRET_KEY: str = "changeme"
    CLERK_SECRET_KEY: str = "placeholder"
    CLERK_PUBLISHABLE_KEY: str = "placeholder"


settings = Settings()