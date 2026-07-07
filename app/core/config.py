from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    cors_origins: list[str] = [
        "http://localhost:3001"
    ]
    
    cache_url: str
    ai_api_key: str
    
    db_name: str
    db_user: str
    db_password: str
    mongo_url: str
    
    algorithm: str = "HS512"
    token_expire: int = 30

    class Config:
        env_file = ".env"


settings = Settings()
