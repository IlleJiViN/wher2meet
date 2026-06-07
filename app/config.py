import os

class Settings:
    DATABASE_URL: str = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/spotsync")
    ES_URL: str = os.environ.get("ES_URL", "http://localhost:9200")
    KAKAO_API_KEY: str = os.environ.get("KAKAO_API_KEY", "7b7cb3eb311174538e017186a7f9ab21")

settings = Settings()
