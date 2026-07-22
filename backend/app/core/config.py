from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    environment: str = "development"
    database_url: str = "sqlite:///./app.db"
    secret_key: str = "change-me"
    next_public_api_base_url: str = "http://127.0.0.1:8000"

    # Optional external providers later
    openai_api_key: str | None = None
    attom_api_key: str | None = None
    rentcast_api_key: str | None = None
    estated_api_key: str | None = None
    regrid_api_key: str | None = None
    google_maps_api_key: str | None = None
    fema_api_key: str | None = None
    noaa_api_key: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
