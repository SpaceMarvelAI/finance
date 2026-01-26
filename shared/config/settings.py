"""
Configuration Settings for Financial Automation System
Handles environment variables and system-wide configurations
"""

import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass


@dataclass
class DatabaseConfig:
    """Database configuration"""
    host: str = os.getenv("DB_HOST", "localhost")
    port: int = int(os.getenv("DB_PORT", "5432"))
    username: str = os.getenv("DB_USERNAME", "postgres")
    password: str = os.getenv("DB_PASSWORD", "postgres")
    database: str = os.getenv("DB_NAME", "financial_automation")
    
    @property
    def connection_string(self) -> str:
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class VectorStoreConfig:
    """Vector store configuration"""
    persist_directory: str = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")
    collection_name: str = "financial_documents"
    embedding_model: str = "all-MiniLM-L6-v2"


@dataclass
class LLMConfig:
    """LLM configuration"""
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    model_name: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
    temperature: float = 0.1
    max_tokens: int = 8192


@dataclass
class StorageConfig:
    """File storage configuration"""
    upload_dir: str = os.getenv("UPLOAD_DIR", "./data/uploads")
    reports_dir: str = os.getenv("REPORTS_DIR", "./data/reports")
    max_file_size_mb: int = 50


@dataclass
class ChunkingConfig:
    """Document chunking configuration"""
    max_chunk_size: int = 1000
    chunk_overlap: int = 200
    min_chunk_size: int = 100


class Settings:
    """Main settings class"""
    
    def __init__(self):
        self.database = DatabaseConfig()
        self.vector_store = VectorStoreConfig()
        self.llm = LLMConfig()
        self.storage = StorageConfig()
        self.chunking = ChunkingConfig()
        
        # Create directories if they don't exist
        self._create_directories()
    
    def _create_directories(self):
        """Create necessary directories"""
        Path(self.storage.upload_dir).mkdir(parents=True, exist_ok=True)
        Path(self.storage.reports_dir).mkdir(parents=True, exist_ok=True)
        Path(self.vector_store.persist_directory).mkdir(parents=True, exist_ok=True)



# Global settings instance
settings = Settings()

def get_settings() -> Settings:
    """Return the global settings instance (for compatibility)"""
    return settings