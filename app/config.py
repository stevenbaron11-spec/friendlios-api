from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    database_url: str = Field(..., alias="DATABASE_URL")
    supabase_url: str = Field(..., alias="SUPABASE_URL")
    supabase_anon_key: str = Field(..., alias="SUPABASE_ANON_KEY")
    supabase_service_key: str | None = Field(None, alias="SUPABASE_SERVICE_KEY")

    photos_bucket: str = Field("photos", alias="PHOTOS_BUCKET")
    public_bucket: bool = Field(True, alias="PUBLIC_BUCKET")

    embedder_backend: str = Field("random", alias="EMBEDDER_BACKEND")  # "random" | "onnx"
    embed_model_path: str = Field("models/dogid.onnx", alias="EMBED_MODEL_PATH")
    embed_vector_size: int = Field(512, alias="EMBED_VECTOR_SIZE")

    api_host: str = Field("0.0.0.0", alias="API_HOST")
    api_port: int = Field(8080, alias="API_PORT")
    log_level: str = Field("info", alias="LOG_LEVEL")

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
