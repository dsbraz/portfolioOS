from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    secret_key: str = "dev-secret-key-change-in-production"
    access_token_expire_minutes: int = 60

    class Config:
        env_file = ".env"


settings = Settings()
