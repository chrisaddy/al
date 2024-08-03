import typer
from al import note, chat
import asyncio

app = typer.Typer(no_args_is_help=True)
app.add_typer(note.app, name="note")


@app.command("chat")
def chat_():
    asyncio.run(chat.run())
