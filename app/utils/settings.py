import os
from platform import system
from dotenv import load_dotenv, find_dotenv


class Settings:
    load_dotenv()

    ENV_FILE = find_dotenv()
    SYSTEM = system()

    # Qdrant Cloud configuration
    QDRANT_URL = os.getenv("QDRANT_URL")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

    # Legacy local configuration (kept for backward compatibility)
    QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT = os.getenv("QDRANT_PORT", "6333")


settings = Settings()
