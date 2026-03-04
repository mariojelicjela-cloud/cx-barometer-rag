import os
from dataclasses import dataclass

@dataclass
class Settings:
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/cxbarometer",
    )

settings = Settings()
