from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    secret_key: str
    access_token_expire_minutes: int = 60
    cors_origins: list[str] = ["http://localhost:4200"]
    environment: str = "development"
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_pre_ping: bool = True

    class Config:
        env_file = ".env"


settings = Settings()
