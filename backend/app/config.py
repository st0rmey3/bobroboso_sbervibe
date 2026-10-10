from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All configuration comes from env (.env in docker compose). Defaults are for local dev only."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://app:app@localhost:5432/app"
    storage_dir: str = "/data/files"
    max_upload_mb: int = 20
    max_files_per_application: int = 40
    max_application_mb: int = 200

    # OIDC (Keycloak)
    oidc_issuer: str = "http://localhost:8080/realms/docs"
    oidc_jwks_url: str = "http://keycloak:8080/realms/docs/protocol/openid-connect/certs"
    oidc_client_id: str = "operator-ui"
    operator_role: str = "operator"

    # LLM
    llm_provider: str = "ollama"  # ollama | gigachat | openai
    llm_timeout_s: float = 180
    ollama_url: str = "http://host.docker.internal:11434"
    ollama_model: str = "qwen2.5vl:7b"
    gigachat_credentials: str = ""
    gigachat_scope: str = "GIGACHAT_API_PERS"
    gigachat_model: str = "GigaChat-2-Max"
    gigachat_verify_ssl: bool = False
    openai_base_url: str = "https://api.openai.com/v1"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # OCR (separate text-recognition model); "none" = LLM reads images itself
    ocr_provider: str = "none"  # olmocr | none
    ocr_base_url: str = "http://localhost:8000/v1"
    ocr_api_key: str = ""
    ocr_model: str = "allenai/olmOCR-2-7B-1025-FP8"
    ocr_timeout_s: float = 180
    ocr_max_tokens: int = 3000

    # Worker
    worker_concurrency: int = 4
    job_lease_s: int = 300
    job_max_attempts: int = 3


settings = Settings()
