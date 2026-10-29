from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openrouter_api_key: str = ""
    openrouter_model: str = ""
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    kubeconfig_path: str = ""
    kubeconfig_server_host: str = ""
    kubectl_insecure_skip_tls_verify: bool = False
    cors_origins: str = "http://localhost:3000"
    kubectl_timeout_seconds: float = 20.0
    log_tail_lines: int = 120
    openrouter_timeout_seconds: float = 45.0
    require_auth: bool = False

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
