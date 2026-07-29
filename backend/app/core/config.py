from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    environment: str = "development"
    database_url: str = "sqlite:///./app.db"
    secret_key: str = "change-me"
    next_public_api_base_url: str = "http://127.0.0.1:8000"
    cors_origins: str = (
        "http://localhost:3000,http://localhost:3001,"
        "http://127.0.0.1:3000,http://127.0.0.1:3001"
    )

    # External API Keys
    google_api_key: str | None = None
    gemini_model: str = "gemini-3.6-flash"  # FREE! Fast and powerful
    census_api_key: str | None = None  # Free Census data API access

    rentcast_api_key: str | None = None
    rentcast_api_base_url: str = "https://api.rentcast.io/v1"

    rapidapi_key: str | None = None  # RapidAPI Zillow key

    zillapi_key: str | None = None
    zillapi_base_url: str = "https://api.zillapi.com/v1"

    # Demo mode (uses sample data instead of real APIs)
    demo_mode: bool = False  # Set to True to use demo data
    use_rapidapi: bool = True  # Ready for RapidAPI when on home network

    # Cache Settings
    census_cache_days: int = 3650
    rentcast_property_cache_days: int = 30
    rentcast_avm_cache_days: int = 7
    fema_cache_days: int = 365
    google_places_cache_days: int = 30

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def allowed_cors_origins(self) -> list[str]:
        return [
            origin.strip().rstrip("/")
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]


settings = Settings()
