import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Settings:
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@127.0.0.1:5432/cxbarometer",
    )
    OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
    TAVILY_API_KEY: str | None = os.getenv("TAVILY_API_KEY")

settings = Settings()