from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    APP_NAME: str = "My Chat App"
    DEBUG: bool = False
    SECRET_KEY: str = "changeme"

    class Config:
        env_file = ".env"


settings = Settings()