from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_community.chat_message_histories import RedisChatMessageHistory
from pathlib import Path
from uuid import uuid4

from al.experts.kubernetes import Knative
from al.experts.general import General

embeddings = FastEmbedEmbeddings(cache_dir=str(Path.home() / ".cache" / "embeddings"))


def create_chat_history(chat_name: str = None):
    if not chat_name:
        chat_name = str(uuid4())
    print(f"creating chat history: {chat_name}")
    return RedisChatMessageHistory(session_id=chat_name, url="redis://localhost:6379")


experts = {"knative": Knative, "general": General}
