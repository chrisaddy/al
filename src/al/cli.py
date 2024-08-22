import typer
from al import note, chat
from typing_extensions import Annotated

app = typer.Typer(no_args_is_help=True)
app.add_typer(note.app, name="note")


@app.command("chat")
def chat_(expert: Annotated[str, typer.Option(help="expert to use")] = "general"):
    chat.run(expert)
