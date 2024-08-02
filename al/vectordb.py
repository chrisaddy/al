import asyncio
from qdrant_client import AsyncQdrantClient, models
from qdrant_client.http.exceptions import ResponseHandlingException
import typer
from pydantic import BaseModel, Field
from dataclasses import dataclass
from typing import Optional
from qdrant_client.http.models import PointIdsList

from al.config import Config
import os
import uuid

os.environ["TOKENIZERS_PARALLELISM"] = "false"


class Collection(BaseModel):
    name: str


@dataclass
class Document:
    text: str
    id: Optional[int] = None
    score: Optional[float] = None
    metadata: Optional[list[dict]] = None


class VectorDB:
    def __init__(self, config: Config = Config()):
        self.config = config
        self.client = None

    async def connect(self):
        if self.client is None:
            try:
                self.client = AsyncQdrantClient(
                    url=self.config.QDRANT_URL, api_key=self.config.QDRANT_API_KEY
                )
            except ResponseHandlingException as e:
                typer.echo(f"Failed to connect to Qdrant: {e}")
                raise typer.Exit(code=1)

    async def add(self, collection: Collection, document: Document):
        if not document.id:
            await self.client.add(
                collection_name=collection.name,
                documents=[document.text],
                metadata=[document.metadata],
            )
            return
        await self.client.add(
            collection_name=collection.name,
            documents=[document.text],
            ids=[document.id],
            metadata=[document.metadata],
        )

    async def delete(self, collection: Collection, document: Document):
        await self.client.delete(
            collection_name=collection.name,
            points_selector=PointIdsList(points=[document.id]),
        )

    async def search(
        self,
        collection: Collection,
        query: str,
        filter: Optional[dict] = None,
        limit: int = 100,
    ):
        if filter:
            results = await self.client.query(
                collection_name=collection.name,
                query_text=query,
                limit=limit,
                query_filter=filter,
            )
        else:
            results = await self.client.query(
                collection_name=collection.name, query_text=query, limit=limit
            )
        return [
            Document(text=r.document.strip(), id=r.id, score=r.score) for r in results
        ]
