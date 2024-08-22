import os
from al.vectordb import NoteStore, Document
import typer
import readline

from al.config import Config
from al import create_chat_history, experts
from al.experts import ask_expert
from langchain.schema import AIMessage
from rich import print
from rich.markdown import Markdown
from rich.console import Console
from rich.prompt import Prompt
from rich.progress import track

console = Console()

config = Config()


app = typer.Typer(no_args_is_help=True)


note_store = NoteStore()


readline.parse_and_bind('"\x0c": clear-screen')  # ctrl+l to clear the screen
readline.parse_and_bind(
    '"\x10": previous-history'
)  # ctrl+p to show previous command(s)


def run(expert: str = None):
    typer.echo(f"starting chat with {expert=}")
    history = create_chat_history(expert)
    expert = experts[expert]

    context = []
    while True:
        user_input = input("> ")

        match user_input.lower():
            case "exit" | "quit":
                break
            case "save":
                with open("chat.history", "w") as f:
                    f.write(str(history.messages))
                continue
            case "load":
                typer.echo("TODO: ability to load chat history")
                continue
            case "clear":
                history.clear()
                continue
            case "history":
                for message in history.messages:
                    if message.type == "ai":
                        preview = (
                            f"[yellow]\[{message.type}][/yellow] {message.content}"
                        )
                    else:
                        preview = f"[blue]\[{message.type}][/blue] {message.content}"
                    total = message.type + message.content
                    if len(total) > 100:
                        preview = preview[:100] + "..."
                    console.print(preview)
                continue
            case "context":
                context_ = [con.split("\n}")[0] for con in context]
                typer.echo(context_)
                continue

        context = [doc[0].page_content for doc in note_store.search(user_input, k=10)]

        history.add_user_message(user_input)

        with console.status("thinking...", spinner="dots3"):
            response = ask_expert(
                user_input,
                expert,
                context="\n".join(context),
                history=str(history.messages),
            ).answer

        console.print(Markdown(response))

        response = response = AIMessage(content=response)
        history.add_ai_message(response)
