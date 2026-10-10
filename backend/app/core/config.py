from functools import lru_cache
from pathlib import Path
from typing import List, Union
from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application runtime configuration managed via environment variables."""

    PROJECT_NAME: str = "The Lenny Growth Assistant"
    VERSION: str = "0.1.0"
    DESCRIPTION: str = (
        "AI-powered growth assistant operationalizing podcast and newsletter insights."
    )
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # Server Bind Settings
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000

    # Knowledge Base / Transcript Storage
    TRANSCRIPTS_DIR: str = Field(
        default="data/transcripts",
        validation_alias=AliasChoices("TRANSCRIPTS_DIR", "DATA_TRANSCRIPTS_DIR"),
    )

    # LLM Provider Configuration ('ollama' or 'anthropic')
    LLM_PROVIDER: str = Field(
        default="ollama",
        validation_alias=AliasChoices("LLM_PROVIDER", "DEFAULT_LLM_PROVIDER"),
    )

    # Ollama Local Service Configuration
    OLLAMA_BASE_URL: str = Field(
        default="http://localhost:11434",
        validation_alias=AliasChoices("OLLAMA_BASE_URL", "OLLAMA_HOST"),
    )
    OLLAMA_MODEL: str = Field(
        default="llama3:8b",
        validation_alias=AliasChoices("OLLAMA_MODEL"),
    )
    OLLAMA_TIMEOUT_SECONDS: float = Field(default=30.0)

    # Cloud Provider (Anthropic) Configuration
    ANTHROPIC_API_KEY: Union[str, None] = Field(
        default=None,
        validation_alias=AliasChoices("ANTHROPIC_API_KEY"),
    )
    ANTHROPIC_MODEL: str = Field(
        default="claude-3-5-sonnet-20241022",
        validation_alias=AliasChoices("ANTHROPIC_MODEL", "AGENT_MODEL"),
    )
    ANTHROPIC_TIMEOUT_SECONDS: float = Field(default=30.0)

    # Agent & Grounded Chat Settings
    AGENT_FRAMEWORK: str = Field(
        default="anthropic_tool_agent",
        validation_alias=AliasChoices("AGENT_FRAMEWORK", "AGENT_SDK"),
    )
    PI_CLI_PATH: Union[str, None] = Field(
        default=None,
        validation_alias=AliasChoices("PI_CLI_PATH", "PI_EXECUTABLE_PATH"),
    )
    PI_TIMEOUT_SECONDS: float = Field(default=30.0)
    PI_CONFIG_DIR: Union[str, None] = Field(
        default=None,
        validation_alias=AliasChoices("PI_CONFIG_DIR", "PI_AGENT_DIR"),
    )
    CHAT_SEARCH_LIMIT: int = Field(default=4)
    MAX_HISTORY_TURNS: int = Field(default=6)

    # Database Settings
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "lenny_growth"
    DATABASE_URL: Union[str, None] = Field(
        default=None,
        validation_alias=AliasChoices("DATABASE_URL", "POSTGRES_URL"),
    )

    # CORS configuration: accepts either BACKEND_CORS_ORIGINS or CORS_ORIGINS from .env
    BACKEND_CORS_ORIGINS: Union[List[str], str] = Field(
        default=["*"],
        validation_alias=AliasChoices("BACKEND_CORS_ORIGINS", "CORS_ORIGINS"),
    )

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.strip() == "*":
                return ["*"]
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        if isinstance(v, list):
            return v
        return ["*"]

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_database_url(cls, v: Union[str, None]) -> Union[str, None]:
        if isinstance(v, str) and v.strip():
            url = v.strip()
            if url.startswith("postgres://"):
                return url.replace("postgres://", "postgresql+psycopg://", 1)
            elif url.startswith("postgresql://"):
                return url.replace("postgresql://", "postgresql+psycopg://", 1)
            elif url.startswith("postgresql+asyncpg://"):
                return url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
            return url
        return None

    @property
    def sync_database_url(self) -> str:
        """Return assembled SQLAlchemy database connection string."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def transcripts_path(self) -> Path:
        """Resolve transcripts directory path relative to project root or absolute path."""
        p = Path(self.TRANSCRIPTS_DIR)
        if p.is_absolute():
            return p
        if p.exists():
            return p.resolve()
        parent_p = Path("..") / p
        if parent_p.exists():
            return parent_p.resolve()
        # Fallback to root relative to this file
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        return (project_root / p).resolve()

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings instance."""
    return Settings()
