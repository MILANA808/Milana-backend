"""
AKSI Configuration Module
=========================

Centralized configuration with environment variable support.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class AKSISettings(BaseSettings):
    """AKSI system configuration."""

    # API Keys
    openai_api_key: Optional[str] = None
    tavily_api_key: Optional[str] = None
    serper_api_key: Optional[str] = None

    # JWT Settings
    jwt_secret_key: str = "aksi-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30

    # ChromaDB Settings
    chromadb_persist_directory: str = "./chromadb_data"
    chromadb_collection_name: str = "aksi_memory"

    # Quantum Settings
    quantum_max_qubits: int = 1000
    quantum_backend: str = "quimb"  # quimb or qiskit

    # Model Settings
    default_model: str = "gpt-4o"
    vision_model: str = "gpt-4o"

    # Logging
    log_level: str = "INFO"
    enable_verbose_logging: bool = False

    class Config:
        env_prefix = "AKSI_"
        env_file = ".env"
        extra = "allow"


# Global settings instance
settings = AKSISettings()
