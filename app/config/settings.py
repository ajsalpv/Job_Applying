"""
Application Settings - Pydantic Settings for environment configuration
"""
import os
import json
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List, Optional
from functools import lru_cache

# logger = get_logger("settings")  # Removed top-level logger to avoid circularity

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # LLM Configuration
    groq_api_key: str = Field(default="", env="GROQ_API_KEY")
    
    # Model Selection
    fast_model: str = "llama-3.1-8b-instant"
    smart_model: str = "llama-3.3-70b-versatile"
    
    # Google Sheets
    google_sheets_credentials_path: str = Field(
        default="credentials.json",
        env="GOOGLE_SHEETS_CREDENTIALS_PATH"
    )
    google_sheets_credentials_json: Optional[str] = Field(
        default=None, 
        env="SHEETS_JSON"
    )
    google_sheet_id: Optional[str] = Field(default=None, env="GOOGLE_SHEET_ID")
    
    # Browser Settings
    headless_browser: bool = Field(default=True, env="HEADLESS_BROWSER")
    browser_timeout: int = 60000
    
    # Scoring
    min_fit_score: int = Field(default=70, env="MIN_FIT_SCORE")
    
    # Rate Limiting
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
    user_location: str = Field(
        default="Bangalore, Bengaluru, Chennai, Hyderabad, Mumbai, Kochi, Thiruvananthapuram, Kerala, Delhi, Goa, Mohali", 
        env="USER_LOCATION"
    )
    target_roles: str = Field(
        default="AI Engineer, ML Engineer, Machine Learning Engineer, AI Developer, Generative AI Engineer, GenAI Engineer",
        env="TARGET_ROLE"
    )
    experience_years: int = Field(default=1, env="EXPERIENCE_YEARS")
    
    # Email API
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

    def save_dynamic_settings(self):
        """Save dynamic settings to a local JSON file for persistence across restarts"""
        data_dir = "app/data"
        os.makedirs(data_dir, exist_ok=True)
        settings_path = os.path.join(data_dir, "dynamic_settings.json")
        
        dynamic_data = {
            "user_location": self.user_location,
            "experience_years": self.experience_years,
            "target_roles": self.target_roles,
        }
        
        try:
            with open(settings_path, 'w') as f:
                json.dump(dynamic_data, f, indent=2)
            print(f"💎 [SETTINGS] Dynamic settings saved to {settings_path}")
        except Exception as e:
            print(f"⚠️ [SETTINGS] Failed to save dynamic settings: {e}")

    @classmethod
    def load_dynamic_settings(cls):
        """Load dynamic settings from file if they exist"""
        settings_path = "app/data/dynamic_settings.json"
        if os.path.exists(settings_path):
            try:
                with open(settings_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ [SETTINGS] Failed to load dynamic settings: {e}")
        return {}


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance with dynamic overrides"""
    settings = Settings()
    # Apply dynamic overrides
    overrides = Settings.load_dynamic_settings()
    for key, value in overrides.items():
        if hasattr(settings, key):
            setattr(settings, key, value)
    return settings
