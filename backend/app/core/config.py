"""
Configuration settings for DocXP
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from pathlib import Path

class Settings(BaseSettings):
    """Application settings"""
    
    # Base directory
    BASE_DIR: Path = Path(__file__).parent.parent
    
    # Application
    APP_NAME: str = "DocXP"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # API
    API_PREFIX: str = "/api"
    API_TIMEOUT: int = 300  # 5 minutes for long operations
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./docxp.db"
    
    # Vector Database Configuration
    VECTOR_DB_TYPE: str = Field(default="chromadb", env="VECTOR_DB_TYPE")  # chromadb | postgresql_pgvector
    VECTOR_DB_PATH: str = "./data/vector_db"  # For ChromaDB
    VECTOR_DB_ENABLED: bool = True
    
    # Embedding Configuration
    EMBEDDING_PROVIDER: str = Field(default="codebert", env="EMBEDDING_PROVIDER")  # codebert | bedrock
    EMBEDDING_MODEL: str = "microsoft/codebert-base"  # For local CodeBERT
    EMBEDDING_DIMENSIONS: int = 768  # CodeBERT: 768, Bedrock Titan: 1024
    
    # AWS Bedrock Configuration
    BEDROCK_EMBED_MODEL_ID: str = Field(default="amazon.titan-embed-text-v2:0", env="BEDROCK_EMBED_MODEL_ID")
    BEDROCK_EMBEDDING_DIMENSIONS: int = Field(default=1024, env="BEDROCK_EMBEDDING_DIMENSIONS")
    AWS_REGION: str = Field(default="us-east-1", env="AWS_REGION")
    
    # PostgreSQL Vector Configuration
    POSTGRESQL_VECTOR_URL: Optional[str] = Field(default=None, env="POSTGRESQL_VECTOR_URL")
    PGVECTOR_ENABLED: bool = Field(default=False, env="PGVECTOR_ENABLED")
    
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
    AWS_ACCESS_KEY_ID: Optional[str] = Field(default=None, env="AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(default=None, env="AWS_SECRET_ACCESS_KEY")
    AWS_SESSION_TOKEN: Optional[str] = Field(default=None, env="AWS_SESSION_TOKEN")
    AWS_PROFILE: Optional[str] = Field(default=None, env="AWS_PROFILE")
    # Bedrock Model Configuration - Choose between Claude 3.5 Sonnet v2 or Claude 3.7 Sonnet
    # us.anthropic.claude-3-5-sonnet-20241022-v2:0 (default)
    # us.anthropic.claude-3-7-sonnet-20250219-v1:0 
    BEDROCK_MODEL_ID: str = Field(default="us.anthropic.claude-3-5-sonnet-20241022-v2:0", env="BEDROCK_MODEL_ID")
    
    # Neo4j Knowledge Graph Configuration
    NEO4J_URI: str = Field(default="bolt://localhost:7687", env="NEO4J_URI")
    NEO4J_USERNAME: str = Field(default="neo4j", env="NEO4J_USERNAME")
    NEO4J_PASSWORD: str = Field(default="docxp-neo4j-2024", env="NEO4J_PASSWORD")
    NEO4J_DATABASE: str = Field(default="neo4j", env="NEO4J_DATABASE")
    NEO4J_MAX_CONNECTION_LIFETIME: int = Field(default=300, env="NEO4J_MAX_CONNECTION_LIFETIME")  # 5 minutes
    NEO4J_MAX_CONNECTION_POOL_SIZE: int = Field(default=50, env="NEO4J_MAX_CONNECTION_POOL_SIZE")
    NEO4J_CONNECTION_ACQUISITION_TIMEOUT: int = Field(default=60, env="NEO4J_CONNECTION_ACQUISITION_TIMEOUT")  # seconds
    NEO4J_ENABLED: bool = Field(default=True, env="NEO4J_ENABLED")
    
    # Redis Configuration (for task queues and caching)
    REDIS_URL: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    RQ_REDIS_URL: str = Field(default="redis://localhost:6379", env="RQ_REDIS_URL")
    REDIS_HOST: str = Field(default="localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, env="REDIS_PORT")
    REDIS_DB: int = Field(default=0, env="REDIS_DB")
    REDIS_PASSWORD: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    REDIS_ENABLED: bool = Field(default=True, env="REDIS_ENABLED")
    
    # API Configuration
    API_PORT: int = Field(default=8001, env="API_PORT")
    AUTH_ENABLED: bool = Field(default=False, env="AUTH_ENABLED")
    
    # Application Environment
    APP_ENV: str = Field(default="development", env="APP_ENV")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Chat/LLM Configuration
    CHAT_MODEL: str = Field(default="anthropic.claude-3-5-sonnet-20241022-v2:0", env="CHAT_MODEL")
    
    # OpenSearch Configuration (Optional)
    OPENSEARCH_HOST: str = Field(default="localhost", env="OPENSEARCH_HOST")
    OPENSEARCH_PORT: int = Field(default=9200, env="OPENSEARCH_PORT")
    OPENSEARCH_USE_SSL: bool = Field(default=False, env="OPENSEARCH_USE_SSL")
    OPENSEARCH_VERIFY_CERTS: bool = Field(default=False, env="OPENSEARCH_VERIFY_CERTS")
    OPENSEARCH_INDEX_NAME: str = Field(default="docxp-code-index", env="OPENSEARCH_INDEX_NAME")
    OPENSEARCH_URL: str = Field(default="http://localhost:9200", env="OPENSEARCH_URL")
    
    # AWS Configuration (Alternate naming)
    AWS_DEFAULT_REGION: Optional[str] = Field(default=None, env="AWS_DEFAULT_REGION")
    AWS_API_TIMEOUT: int = Field(default=30, env="AWS_API_TIMEOUT")
    
    # Processing Configuration
    MAX_CONCURRENT_CHUNKS: int = Field(default=4, env="MAX_CONCURRENT_CHUNKS")
    MAX_RETRIES: int = Field(default=3, env="MAX_RETRIES")
    
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
    
    # Repository Processing
    MAX_CONCURRENT_REPOS: int = 4  # Maximum repositories to process in parallel
    BATCH_SIZE: int = 50  # Files processed per batch
    
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
        env_file = [".env.enterprise", ".env"]  # Try .env.enterprise first, then .env
        case_sensitive = True

settings = Settings()

# Note: Directory creation moved to application startup to avoid import-time side effects
