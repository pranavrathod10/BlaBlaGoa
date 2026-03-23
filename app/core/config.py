from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    APP_NAME: str = "BlaBlaGoa"
    DEBUG: bool = False
    SECRET_KEY: str = "changeme"
    CLERK_SECRET_KEY: str
    CLERK_PUBLISHABLE_KEY: str

    class Config:
        env_file = ".env"


settings = Settings()