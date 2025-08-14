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
    
    # External Database Analysis (Optional - graceful degradation if not available)
    # Oracle Database
    ORACLE_HOST: Optional[str] = Field(default=None, env="ORACLE_HOST")
    ORACLE_PORT: int = Field(default=1521, env="ORACLE_PORT")
    ORACLE_SERVICE: Optional[str] = Field(default=None, env="ORACLE_SERVICE")
    ORACLE_USERNAME: Optional[str] = Field(default=None, env="ORACLE_USERNAME")
    ORACLE_PASSWORD: Optional[str] = Field(default=None, env="ORACLE_PASSWORD")
    
    # PostgreSQL Database
    POSTGRES_HOST: Optional[str] = Field(default=None, env="POSTGRES_HOST")
    POSTGRES_PORT: int = Field(default=5432, env="POSTGRES_PORT")
    POSTGRES_DATABASE: Optional[str] = Field(default=None, env="POSTGRES_DATABASE")
    POSTGRES_USERNAME: Optional[str] = Field(default=None, env="POSTGRES_USERNAME")
    POSTGRES_PASSWORD: Optional[str] = Field(default=None, env="POSTGRES_PASSWORD")
    POSTGRES_URL: Optional[str] = Field(default=None, env="POSTGRES_URL")  # Alternative full URL
    
    # MySQL Database
    MYSQL_HOST: Optional[str] = Field(default=None, env="MYSQL_HOST")
    MYSQL_PORT: int = Field(default=3306, env="MYSQL_PORT")
    MYSQL_DATABASE: Optional[str] = Field(default=None, env="MYSQL_DATABASE")
    MYSQL_USERNAME: Optional[str] = Field(default=None, env="MYSQL_USERNAME")
    MYSQL_PASSWORD: Optional[str] = Field(default=None, env="MYSQL_PASSWORD")
    MYSQL_URL: Optional[str] = Field(default=None, env="MYSQL_URL")  # Alternative full URL
    
    # SQL Server Database
    SQLSERVER_HOST: Optional[str] = Field(default=None, env="SQLSERVER_HOST")
    SQLSERVER_PORT: int = Field(default=1433, env="SQLSERVER_PORT")
    SQLSERVER_DATABASE: Optional[str] = Field(default=None, env="SQLSERVER_DATABASE")
    SQLSERVER_USERNAME: Optional[str] = Field(default=None, env="SQLSERVER_USERNAME")
    SQLSERVER_PASSWORD: Optional[str] = Field(default=None, env="SQLSERVER_PASSWORD")
    SQLSERVER_URL: Optional[str] = Field(default=None, env="SQLSERVER_URL")  # Alternative full URL
    
    # Database Analysis Configuration
    DB_CONNECTION_TIMEOUT: int = Field(default=10, env="DB_CONNECTION_TIMEOUT")  # seconds
    DB_QUERY_TIMEOUT: int = Field(default=30, env="DB_QUERY_TIMEOUT")  # seconds
    ENABLE_DB_ANALYSIS: bool = Field(default=True, env="ENABLE_DB_ANALYSIS")  # Can disable entirely
    
    # AWS Bedrock - Support multiple authentication methods
    AWS_REGION: str = Field(default="us-east-1", env="AWS_REGION")
    AWS_ACCESS_KEY_ID: Optional[str] = Field(default=None, env="AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(default=None, env="AWS_SECRET_ACCESS_KEY")
    AWS_SESSION_TOKEN: Optional[str] = Field(default=None, env="AWS_SESSION_TOKEN")
    AWS_PROFILE: Optional[str] = Field(default=None, env="AWS_PROFILE")
    # Bedrock Model Configuration - Choose between Claude 3.5 Sonnet v2 or Claude 3.7 Sonnet
    # us.anthropic.claude-3-5-sonnet-20241022-v2:0 (default)
    # us.anthropic.claude-3-7-sonnet-20250219-v1:0 
    BEDROCK_MODEL_ID: str = Field(default="us.anthropic.claude-3-5-sonnet-20241022-v2:0", env="BEDROCK_MODEL_ID")
    
    # Feature flags
    
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
