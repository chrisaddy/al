import os
import json
from pydantic import BaseSettings


class Config(BaseSettings):
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY")
    QDRANT_API_KEY: str = os.getenv("QDRANT_API_KEY")
    QDRANT_URL: str = os.getenv("QDRANT_URL")

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
