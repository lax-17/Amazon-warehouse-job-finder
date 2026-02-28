"""Configuration management for Amazon Jobs Monitor v2."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

try:
    from dotenv import load_dotenv
    # Load from config.env in the project directory
    config_path = Path(__file__).parent.parent / "config.env"
    if config_path.exists():
        load_dotenv(config_path)
    else:
        load_dotenv()  # Fall back to default .env file
except ImportError:
    pass


@dataclass
class Config:
    """Application configuration."""
    
    # API Configuration
    amazon_jobs_token: str = ""
    amazon_api_url: str = "https://qy64m4juabaffl7tjakii4gdoa.appsync-api.eu-west-1.amazonaws.com/graphql"
    
    # Database
    database_path: str = "data/jobs.db"
    
    # Monitoring Settings
    poll_interval_seconds: float = 60.0
    max_historical_days: int = 30
    
    # Search Defaults
    default_location: str = "Leeds, UK"
    default_radius_miles: float = 50.0
    default_job_type: str = "part-time"
    
    # Logging
    log_level: str = "INFO"
    log_to_console: bool = True
    log_file: str = "data/monitor.log"
    
    # Web Dashboard
    web_host: str = "127.0.0.1"
    web_port: int = 5000
    web_debug: bool = False
    
    # Notifications (optional)
    email_smtp_server: str = ""
    email_smtp_port: int = 587
    email_username: str = ""
    email_password: str = ""
    email_to: str = ""
    
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    
    def __post_init__(self):
        """Load configuration from environment variables."""
        self.amazon_jobs_token = os.getenv("AMAZON_JOBS_TOKEN", self.amazon_jobs_token)
        
        self.database_path = os.getenv("DATABASE_PATH", self.database_path)
        
        self.poll_interval_seconds = float(os.getenv(
            "POLL_INTERVAL_SECONDS", self.poll_interval_seconds
        ))
        self.max_historical_days = int(os.getenv(
            "MAX_HISTORICAL_DAYS", self.max_historical_days
        ))
        
        self.default_location = os.getenv("DEFAULT_LOCATION", self.default_location)
        self.default_radius_miles = float(os.getenv(
            "DEFAULT_RADIUS_MILES", self.default_radius_miles
        ))
        self.default_job_type = os.getenv("DEFAULT_JOB_TYPE", self.default_job_type)
        
        self.log_level = os.getenv("LOG_LEVEL", self.log_level)
        self.log_to_console = os.getenv(
            "LOG_TO_CONSOLE", "true" if self.log_to_console else "false"
        ).lower() in ("true", "1", "yes", "y")
        
        self.web_host = os.getenv("WEB_HOST", self.web_host)
        self.web_port = int(os.getenv("WEB_PORT", self.web_port))
        self.web_debug = os.getenv(
            "WEB_DEBUG", "true" if self.web_debug else "false"
        ).lower() in ("true", "1", "yes", "y")
        
        self.email_smtp_server = os.getenv("EMAIL_SMTP_SERVER", self.email_smtp_server)
        self.email_smtp_port = int(os.getenv("EMAIL_SMTP_PORT", self.email_smtp_port))
        self.email_username = os.getenv("EMAIL_USERNAME", self.email_username)
        self.email_password = os.getenv("EMAIL_PASSWORD", self.email_password)
        self.email_to = os.getenv("EMAIL_TO", self.email_to)
        
        self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", self.telegram_bot_token)
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", self.telegram_chat_id)
        
        # Ensure data directory exists
        Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)
        Path(self.log_file).parent.mkdir(parents=True, exist_ok=True)
    
    def get_token(self) -> str:
        """Get bearer token from various sources."""
        if self.amazon_jobs_token:
            return self.amazon_jobs_token
        
        # Try loading from token files
        token_files = [
            ".amazon_jobs_token",
            "amazon_jobs_token.txt",
            os.path.expanduser("~/.amazon_jobs_token"),
        ]
        
        for file_path in token_files:
            if os.path.exists(file_path):
                with open(file_path, "r") as f:
                    token = f.read().strip()
                    if token:
                        return token
        
        raise ValueError(
            "No Amazon Jobs token found. Set AMAZON_JOBS_TOKEN environment variable "
            "or create a .amazon_jobs_token file."
        )
