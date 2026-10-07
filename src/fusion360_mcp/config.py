import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


@dataclass(frozen=True)
class Settings:
    host: str = os.getenv("FUSION_HOST", "127.0.0.1")
    port: int = int(os.getenv("FUSION_PORT", "9876"))
    timeout: float = float(os.getenv("FUSION_TIMEOUT", "30.0"))


settings = Settings()
