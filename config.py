"""
ModPulse configuration — loaded from environment variables.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    REDDIT_CLIENT_ID: str = ""
    REDDIT_CLIENT_SECRET: str = ""
    REDDIT_USER_AGENT: str = "ModPulse/0.1.0 by u/modpulse_dev"

    TARGET_SUBREDDITS: str = "python,datascience"

    SPIKE_THRESHOLD: float = 2.5
    NEW_ACCOUNT_RATIO: float = 0.4

    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    ALERT_EMAIL: str = ""

    DATABASE_URL: str = "sqlite:///./modpulse.db"

    class Config:
        env_file = ".env"


settings = Settings()
