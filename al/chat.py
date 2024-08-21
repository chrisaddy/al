from al.vectordb import NoteStore, Document
import typer

from al.config import Config
from al import create_chat_history, experts
from al.experts import ask_expert


config = Config()


app = typer.Typer(no_args_is_help=True)


store = NoteStore("notes")


def summarize_chat(memory: list[tuple[str, str]]):
    """You are summarizing a chat between a user and AI Assistant."""
    return f"<Chat History>{memory}</Chat History><Summary>"


def run(expert: str = None):
    typer.echo(f"starting chat with {expert=}")
    history = create_chat_history(expert)
    expert = experts[expert]

    while True:
        user_input = input("> ")

        match user_input.lower():
            case "exit" | "quit":
                break
            case "save":
                with open("chat.history", "w") as f:
                    f.write(str(history.messages))
                    history.clear()
            case "load":
                typer.echo("TODO: ability to load chat history")
                continue
            case "history":
                typer.echo(history.messages)
                continue

        history.add_user_message(user_input)

        response = ask_expert(user_input, expert, history=str(history.messages)).answer
        history.add_ai_message(response)
        typer.echo(response)
