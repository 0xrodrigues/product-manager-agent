from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    llm_base_url: str
    llm_api_key: str
    llm_model: str
    atlassian_base_url: str = ""
    atlassian_user_email: str = ""
    atlassian_api_token: str = ""
    atlassian_ssl_verify: bool = True
    jira_enabled: bool = False
    jira_project_key: str = ""
    confluence_enabled: bool = False


settings = Settings()
