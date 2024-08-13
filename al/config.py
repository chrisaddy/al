import os
import json
from pydantic import BaseSettings


class Config(BaseSettings):
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY")
    QDRANT_API_KEY: str = os.getenv("QDRANT_API_KEY")
    QDRANT_URL: str = os.getenv("QDRANT_URL")
    AL_TURSO_URL: str = os.getenv("AL_TURSO_URL")
    AL_TURSO_TOKEN: str = os.getenv("AL_TURSO_TOKEN")

    @classmethod
    def load(cls):
        config_path = os.path.expanduser("~/.al/config.json")
        if not os.path.exists(config_path):
            with open(config_path, "w") as f:
                json.dump({}, f)
        with open(config_path, "r") as f:
            data = json.load(f)
        return cls(**data)

    def save(self):
        config_path = os.path.expanduser("~/.al/config.json")
        with open(config_path, "w") as f:
            json.dump(self.dict(), f, indent=4)

    @property
    def ell_store(self):
        if self.AL_TURSO_URL and self.AL_TURSO_TOKEN:
            return f"sqlite+{self.AL_TURSO_URL}?authToken={self.AL_TURSO_TOKEN}"
        return None
