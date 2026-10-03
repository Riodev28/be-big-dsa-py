from pydantic_settings import BaseSettings
from pydantic import SecretStr


class Settings(BaseSettings):
    cors_origins: list[str] = ["http://localhost:3001"]

    cache_url: str
    ai_api_key: SecretStr
    
    db_name: str
    db_user: str
    db_password: str
    mongo_url: str
    
    jwt_secret_key: SecretStr
    algorithm: str = "HS512"
    token_expire: int = 30
    refresh_token_expire_days: int = 7

    class Config:
        env_file = ".env"


settings = Settings()
