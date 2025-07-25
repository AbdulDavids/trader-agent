from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_key: Optional[str] = None
    
    # OpenAI Configuration
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379"
    stock_data_cache_ttl: int = 43200  # 12 hours
    analysis_cache_ttl: int = 86400    # 24 hours
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    
    # Market Data Configuration
    yfinance_timeout: int = 30
    
    # Logging
    log_level: str = "INFO"
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8"
    }


settings = Settings()