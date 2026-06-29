from pydantic_settings import BaseSettings


class Configuracoes(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET: str
    JWT_REFRESH_SECRET: str
    JWT_EXPIRES_MINUTES: int = 15
    JWT_REFRESH_EXPIRES_DAYS: int = 7
    PORT: int = 8000

    model_config = {"env_file": ".env"}


configuracoes = Configuracoes()
