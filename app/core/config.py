from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # App
    PROJECT_NAME: str = "Finance Tracker Bot"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    VERSION: str = "2.0.0"
    
    # Twilio
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_PHONE_NUMBER: str
    
    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "financetracker"
    DATABASE_URL: str | None = None
    
    # Security
    SECRET_KEY: str = "change_this_secret_key_in_production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    LOG_REQUEST_BODY: bool = False
    MAX_LOG_BODY_SIZE: int = 1000
    LOG_ROTATION_MAX_SIZE: int = 10 * 1024 * 1024  # 10MB
    LOG_ROTATION_BACKUP_COUNT: int = 5
    ENABLE_STRUCTURED_LOGGING: bool = True
    ENABLE_CONSOLE_LOGGING: bool = True
    
    # Monitoring Configuration
    ENABLE_METRICS: bool = True
    ENABLE_HEALTH_CHECKS: bool = True
    METRICS_RETENTION_HOURS: int = 24
    HEALTH_CHECK_TIMEOUT_SECONDS: int = 30
    
    # Performance Configuration
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600
    REQUEST_TIMEOUT_SECONDS: int = 60
    
    # Error Handling Configuration
    ENABLE_ERROR_TRACKING: bool = True
    MAX_ERROR_DETAIL_LENGTH: int = 1000
    SENSITIVE_DATA_MASKING: bool = True
    
    # Rate Limiting (if implemented)
    ENABLE_RATE_LIMITING: bool = False
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60
    RATE_LIMIT_BURST_SIZE: int = 10

    model_config = SettingsConfigDict(
        env_file=".env", 
        case_sensitive=True,
        extra='ignore'  # Allow extra fields in .env
    )

    @property
    def create_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT.lower() == "development"
    
    def get_log_level_int(self) -> int:
        """Convert log level string to integer."""
        import logging
        return getattr(logging, self.LOG_LEVEL.upper(), logging.INFO)

settings = Settings()

