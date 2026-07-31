from enum import StrEnum
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Profile(StrEnum):
    HF_SPACE = "HF_SPACE"
    FULL_STACK = "FULL_STACK"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    deployment_profile: Profile = Profile.HF_SPACE
    vector_backend: str = "pgvector"
    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"
    pgvector_url: str | None = None
    milvus_uri: str | None = None
    neo4j_uri: str | None = None
    neo4j_username: str | None = None
    neo4j_password: str | None = None
    admin_debug: bool = False
    request_timeout_seconds: float = 30

    def model_post_init(self, __context):
        if self.vector_backend not in {"pgvector", "milvus", "hybrid"}:
            raise ValueError("VECTOR_BACKEND must be pgvector, milvus, or hybrid")

@lru_cache
def get_settings() -> Settings:
    return Settings()
