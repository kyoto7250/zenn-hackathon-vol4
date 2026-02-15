from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Kubernetes Visualization Simulator"
    DATABASE_URL: str
    GEMINI_API_KEY: str
    KUBERNETES_HOST: str = "http://localhost:8080"

    class Config:
        env_file = ".env"


settings = Settings()
