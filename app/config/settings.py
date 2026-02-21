"""
Application Settings - Pydantic Settings for environment configuration
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List, Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # LLM Configuration
    groq_api_key: str = Field(default="", env="GROQ_API_KEY")
    
    # Model Selection (llama-3.1-8b-instant is ~10x more token-efficient)
    fast_model: str = "llama-3.1-8b-instant"  # For quick tasks (scoring, extraction)
    smart_model: str = "llama-3.3-70b-versatile"  # For writing (resume, cover letter)
    
    # Google Sheets
    google_sheets_credentials_path: str = Field(
        default="credentials.json",
        env="GOOGLE_SHEETS_CREDENTIALS_PATH"
    )
    google_sheets_credentials_json: Optional[str] = Field(
        default=None,
        env="GOOGLE_SHEETS_CREDENTIALS_JSON"
    )
    google_sheet_id: Optional[str] = Field(default=None, env="GOOGLE_SHEET_ID")
    
    # Browser Settings
    headless_browser: bool = Field(default=True, env="HEADLESS_BROWSER")
    browser_timeout: int = 60000  # milliseconds (60 seconds)
    
    # Scoring
    min_fit_score: int = Field(default=70, env="MIN_FIT_SCORE")
    
    # Rate Limiting (requests per minute)
    linkedin_rate_limit: int = Field(default=10, env="LINKEDIN_RATE_LIMIT")
    indeed_rate_limit: int = Field(default=15, env="INDEED_RATE_LIMIT")
    naukri_rate_limit: int = Field(default=15, env="NAUKRI_RATE_LIMIT")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    # Scheduling
    check_interval_minutes: float = Field(default=120.0, env="CHECK_INTERVAL_MINUTES")

    # Notifications
    telegram_bot_token: str = Field(default="", env="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: str = Field(default="", env="TELEGRAM_CHAT_ID")
    
    # SMTP Configuration
    smtp_server: str = Field(default="smtp.gmail.com", env="SMTP_SERVER")
    smtp_port: int = Field(default=587, env="SMTP_PORT")
    smtp_email: Optional[str] = Field(default=None, env="SMTP_EMAIL")
    smtp_password: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    
    # User Profile
    user_name: str = Field(default="Ajsal PV", env="USER_NAME")
    user_email: str = Field(default="pvajsal27@gmail.com", env="USER_EMAIL")
    user_phone: str = Field(default="+91 7356793165", env="USER_PHONE")
    user_location: str = Field(default="Bangalore, Bengaluru, Chennai, Hyderabad, Mumbai, Kochi, Thiruvananthapuram, Kerala, Delhi, Goa, Mohali", env="USER_LOCATION")
    target_roles: str = Field(
        default="AI Engineer,ML Engineer,Machine Learning Engineer",
        env="TARGET_ROLE"
    )
    experience_years: int = Field(default=2, env="EXPERIENCE_YEARS")
    
    # Email API (Recommended for Cloud)
    gmail_credentials_path: str = Field(default="gmail_credentials.json", env="GMAIL_CREDENTIALS_PATH")
    gmail_token_path: str = Field(default="token.json", env="GMAIL_TOKEN_PATH")
    gmail_token_json: Optional[str] = Field(default=None, env="GMAIL_TOKEN_JSON")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
    
    @property
    def target_roles_list(self) -> List[str]:
        """Parse comma-separated roles into list"""
        return [role.strip() for role in self.target_roles.split(",")]


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance"""
    return Settings()
