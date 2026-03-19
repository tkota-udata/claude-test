from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    twitter_api_key: str = ""
    twitter_api_secret: str = ""
    twitter_access_token: str = ""
    twitter_access_token_secret: str = ""
    anthropic_api_key: str = ""
    cors_origin: str = "*"
    database_url: str = "sqlite:///./tweets.db"

    class Config:
        env_file = ".env"


settings = Settings()
