from al.vectordb import Collection
from al.vectordb import VectorDB, Document, search_sync
import typer
import ell
import asyncio

NotesCollection = Collection(name="notes-demo")

app = typer.Typer(no_args_is_help=True)


@ell.lm(model="gpt-4o-mini")
def summarize_chat(memory: list[tuple[str, str]]):
    """You are summarizing a chat between a user and AI Assistant."""
    return f"<Chat History>{memory}</Chat History><Summary>"


async def retriever(query: str):
    db = VectorDB()
    await db.connect()
    return await search_sync(NotesCollection, " ".join(query))


@ell.lm(model="gpt-4o-mini")
def retrieval_augmented_chat(
    query: str, documents: list[Document], memory: list[tuple[str, str]]
):
    """You're going to be given a user query and a set of documents as
    context to the query. You will also be given a list of previous messages
    in the chat. Answer the query using the context."""

    return f"<Chat History>{memory}</Chat History><Context>{documents}</Context><User Query>{query}</Query><Answer>"


async def run():
    ell.config.verbose = True

    db = VectorDB()
    await db.connect()

    memory_buffer = []
    summarize_task = None

    while True:
        user_input = input("> ")
        if user_input.lower() in ["exit", "quit"]:
            break

        if len(memory_buffer) <= 1:
            retrieved = await retriever(user_input)
        else:
            retrieved = []

        response = retrieval_augmented_chat(user_input, retrieved, memory_buffer)
        print(response)

        if len(memory_buffer) >= 15 and summarize_task is None:
            summarize_task = asyncio.create_task(summarize_chat(memory_buffer))

        if summarize_task and summarize_task.done():
            summary = await summarize_task
            memory_buffer = [summary]
            summarize_task = None

        memory_buffer.append((user_input, response))
