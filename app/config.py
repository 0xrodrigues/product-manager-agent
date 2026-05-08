from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    anthropic_api_key: str
    jira_base_url: str
    jira_user_email: str
    jira_api_token: str
    jira_project_key: str


settings = Settings()
