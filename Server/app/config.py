from pydantic_settings import BaseSettings, SettingsConfigDict


# Environments where nothing real is at stake: the demo seed may run, and the
# monthly job may print e-mails instead of sending them.
LOCAL_ENVIRONMENTS = frozenset({"development", "local"})


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    database_url: str
    secret_key: str
    access_token_expire_minutes: int = 60
    cors_origins: list[str] = ["http://localhost:4200"]
    environment: str = "development"
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_pre_ping: bool = True

    # Monthly reporting e-mail (scripts/dispatch_monthly_report.py).
    # `app_base_url` is where the investee opens the form; `console` prints
    # instead of sending, so only an explicit `smtp` reaches anyone.
    app_base_url: str = "http://localhost:4200"
    email_backend: str = "console"
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_sender: str | None = None
    smtp_starttls: bool = True
    # Closes the automatic e-mail (e.g. "Equipe de Portfólio"); blank, it ends
    # at the thanks.
    email_signature: str | None = None


settings = Settings()
