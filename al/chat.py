from al.vectordb import NoteStore, Document
import typer

from al.config import Config


config = Config()


app = typer.Typer(no_args_is_help=True)


store = NoteStore("notes")


def summarize_chat(memory: list[tuple[str, str]]):
    """You are summarizing a chat between a user and AI Assistant."""
    return f"<Chat History>{memory}</Chat History><Summary>"


def retrieval_augmented_chat(
    query: str, documents: list[Document], memory: list[tuple[str, str]]
):
    """You're going to be given a user query and a set of documents as
    context to the query. You will also be given a list of previous messages
    in the chat. Answer the query using the context."""

    return f"<Chat History>{memory}</Chat History><Context>{documents}</Context><User Query>{query}</Query><Answer>"


def run():
    memory_buffer = []
    summarize_task = None

    while True:
        user_input = input("> ")
        if user_input.lower() in ["exit", "quit"]:
            break

        if len(memory_buffer) <= 1:
            relevant_notes = store.search(user_input)
        else:
            relevant_notes = []

        response = retrieval_augmented_chat(user_input, retrieved, memory_buffer)
        print(response)

        if len(memory_buffer) >= 15 and summarize_task is None:
            summarize_task = asyncio.create_task(summarize_chat(memory_buffer))

        if summarize_task and summarize_task.done():
            summary = await summarize_task
            memory_buffer = [summary]
            summarize_task = None

        memory_buffer.append((user_input, response))
