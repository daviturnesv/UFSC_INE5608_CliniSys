from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "INE5608_CliniSys"
    secret_key: str = "chave-misteriosa-troca-ja"
    access_token_expire_minutes: int = 30
    database_url: str = "sqlite+aiosqlite:///./clinisys_uc_admin.db"
    admin_email: str = "admin@exemplo.com"
    admin_password: str = "admin123"

    class Config:
        env_prefix = "APP_"
        case_sensitive = False


settings = Settings()
