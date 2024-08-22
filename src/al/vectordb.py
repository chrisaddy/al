import re
from pathlib import Path

from pydantic import BaseModel
from langchain_community.vectorstores.redis import Redis
from langchain.docstore.document import Document

from al import REDIS_URL, embeddings


class IndexItem(BaseModel):
    index_id: str
    note_id: str
    note_path: Path


class NoteStore:
    def __init__(
        self,
        collection: str = "notes",
        redis_url=REDIS_URL,
        notes_path=Path.home() / "notes",
    ):
        self.collection = collection
        self.redis_url = redis_url
        self.client = Redis(
            index_name=collection,
            embedding=embeddings,
            redis_url=redis_url,
            index_schema=self.index_schema,
        )
        self.notes_path = notes_path

    @property
    def index_schema(self):
        return {
            "tag": [{"name": "tags"}, {"name": "contexts"}, {"name": "projects"}],
            "text": [{"name": "content"}],
        }

    def parse_content(self, note):
        tags = re.findall(r"#(\w+)", note)
        contexts = re.findall(r"@(\w+)", note)
        projects = re.findall(r"\+(\w+)", note)

        return {
            "tags": ",".join(tags),
            "contexts": ",".join(contexts),
            "projects": ",".join(projects),
        }

    def add_note(self, note) -> IndexItem:
        parsed_note = self.parse_content(note)
        document = Document(page_content=note, metadata=parsed_note)
        result = self.client.add_documents([document])

        id_ = result[0]

        note_id = id_.split(":")[-1]
        note_path = Path(self.notes_path) / f"{note_id}.md"
        with open(note_path, "w") as f:
            f.write(note)
        return IndexItem(index_id=id_, note_id=note_id, note_path=note_path)

    def search(self, query, k=50, with_scores=True, limit_score=0.2):
        parsed_query = self.parse_content(query)
        # tags_filter = RedisTag("tags") == parsed_query.get("tags")
        # projects_filter = RedisTag("projects") == parsed_query.get("projects").replace(
        #     ",", "|"
        # )
        # contexts_filter = RedisTag("contexts") == parsed_query.get("contexts").replace(
        #     ",", "|"
        # )
        # filter = tags_filter | contexts_filter | projects_filter
        if with_scores:
            return self.client.similarity_search_with_relevance_scores(
                query,
                score_threshold=limit_score,
                k=k,  # filter=tags_filter
            )
        else:
            return self.client.similarity_search_limit_score(
                query, k=k, score_threshold=limit_score
            )

    def delete_document(self, document) -> IndexItem:
        id_ = document.metadata.get("id")
        note_id = id_.split(":")[-1]
        note_path = Path(self.notes_path) / f"{note_id}.md"

        self.client.delete([id_], redis_url=self.redis_url)
        Path.unlink(note_path)

        return IndexItem(index_id=id_, note_id=note_id, note_path=note_path)


if __name__ == "__main__":
    tmp = Path(".") / "notes"
    vector_store = NoteStore("asdfujsdf", notes_path=tmp)
    # document = vector_store.parse_note(
    # )

    result = vector_store.add_note("hello world +thisproject @abby @willa #house #todo")
    print(f"added {result}")
    result = vector_store.search("#todo +thisproject +other willa house")
    print(f" search result={result}")
    #
    # result = vector_store.delete_document(result[0][0])
    # print(f"deleted {result}")
