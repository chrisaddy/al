import typer
from al import note

app = typer.Typer(no_args_is_help=True)
app.add_typer(note.app, name="note")
