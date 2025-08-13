"""
Configuration settings for DocXP
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from pathlib import Path

class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "DocXP"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # API
    API_PREFIX: str = "/api"
    API_TIMEOUT: int = 300  # 5 minutes for long operations
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./docxp.db"
    
    # AWS Bedrock - Support multiple authentication methods
    AWS_REGION: str = Field(default="us-east-1", env="AWS_REGION")
    AWS_ACCESS_KEY_ID: Optional[str] = Field(default=None, env="AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(default=None, env="AWS_SECRET_ACCESS_KEY")
    AWS_SESSION_TOKEN: Optional[str] = Field(default=None, env="AWS_SESSION_TOKEN")
    AWS_PROFILE: Optional[str] = Field(default=None, env="AWS_PROFILE")
    BEDROCK_MODEL_ID: str = Field(default="anthropic.claude-v2", env="BEDROCK_MODEL_ID")
    
    # Feature flags
    REQUIRE_AWS_CREDENTIALS: bool = Field(default=True, env="REQUIRE_AWS_CREDENTIALS")
    
    # File System
    OUTPUT_DIR: str = "./output"
    TEMP_DIR: str = "./temp"
    CONFIGS_DIR: str = "./configs"
    MAX_FILE_SIZE_MB: int = 100
    
    # Processing
    MAX_WORKERS: int = 4
    CHUNK_SIZE: int = 1000  # Lines per chunk for large files
    PROCESSING_TIMEOUT: int = 600  # 10 minutes
    
    # Documentation Generation
    DEFAULT_DOC_DEPTH: str = "standard"
    INCLUDE_DIAGRAMS: bool = True
    INCLUDE_BUSINESS_RULES: bool = True
    INCLUDE_API_DOCS: bool = True
    
    # Parsing
    SUPPORTED_LANGUAGES: list = ["python", "java", "javascript", "typescript", "perl", "struts", "struts2", "corba", "angular"]
    IGNORE_PATTERNS: list = [
        "*.pyc", "__pycache__", "*.class", 
        "node_modules", ".git", ".venv", 
        "dist", "build", "target"
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

# Create directories if they don't exist
Path(settings.OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.TEMP_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.CONFIGS_DIR).mkdir(parents=True, exist_ok=True)
