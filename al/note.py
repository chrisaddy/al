import os
import subprocess
import typer
from typing import Optional
import uuid
from al.vectordb import VectorDB, Document, search_sync
import asyncio
from pydantic import BaseModel
from pyfzf.pyfzf import FzfPrompt
import tempfile
from pathlib import Path
from qdrant_client import models
from qdrant_client.http.models import Filter
import ell.decorators.lm


from al.vectordb import Collection

app = typer.Typer(no_args_is_help=True)


NotesCollection = Collection(name="notes-demo")


@app.command()
def add():
    asyncio.run(modify_note())


@app.command()
def search(query: Optional[list[str]] = typer.Argument(None, help="query text")):
    if not query:
        query = []
    filter = Filter(
        should=[
            models.FieldCondition(
                key="contexts", match=models.MatchValue(value=context)
            )
            for context in [q for q in query if q.startswith("@")]
        ]
        + [
            models.FieldCondition(key="tags", match=models.MatchValue(value=tag))
            for tag in [q for q in query if q.startswith("#")]
        ]
        + [
            models.FieldCondition(
                key="projects", match=models.MatchValue(value=project)
            )
            for project in [q for q in query if q.startswith("+")]
        ]
    )
    results = asyncio.run(search_sync(NotesCollection, " ".join(query), filter))

    if not results:
        typer.echo("No results found.")
        return

    fzf = FzfPrompt()

    temp_dir = tempfile.mkdtemp()
    temp_files = []
    for doc in results:
        temp_file = Path(temp_dir) / f"{doc.id}.md"
        temp_file.write_text(doc.text)
        temp_files.append(str(temp_file))

    fzf_input = []
    for i, doc in enumerate(results):
        formatted_score = f"{doc.score:.3f}"
        content = doc.text.replace("\n", "\\n")
        fzf_input.append(f"{formatted_score}\t{content}\t{temp_files[i]}")

    fzf_options = (
        "--multi "
        "--with-nth=1,2 "
        "--delimiter='\t' "
        "--preview='bat --color=always --style=numbers {3}' "
        "--preview-window='right:50%:wrap' "
        r"--bind='ctrl-/:change-preview-window(down|hidden|)'"
    )
    selected = fzf.prompt(fzf_input, fzf_options)

    if selected:
        selected_file = selected[0].split("\t")[-1]
        with open(selected_file, "r") as file:
            selected_content = file.read()
            id = selected[0].split("/")[-1].split(".")[0]
        asyncio.run(modify_note(Document(text=selected_content, id=id)))
    else:
        asyncio.run(modify_note())


async def modify_note(document: Optional[Document] = None):
    if not document:
        document = Document(text="", id=str(uuid.uuid4()))
    if not document.id:
        document.id = str(uuid.uuid4())
    if not document.text:
        document.text = ""

    editor = os.getenv("EDITOR", "vi")
    temp_dir = tempfile.mkdtemp()
    temp_file = Path(temp_dir) / f"{document.id}.md"

    with open(temp_file, "w") as file:
        file.write(document.text)

    subprocess.run([editor, temp_file])

    with open(temp_file, "r") as file:
        document.text = file.read()

    tags = [tag for tag in document.text.split() if tag.startswith("#")]
    contexts = [context for context in document.text.split() if context.startswith("@")]
    projects = [project for project in document.text.split() if project.startswith("+")]
    document.metadata = {
        "tags": tags,
        "context": contexts,
        "project": projects,
    }

    db = VectorDB()
    await db.connect()

    if document.id and document.text == "":
        await db.delete(collection=NotesCollection, document=document)
    else:
        await db.add(collection=NotesCollection, document=document)

    os.remove(temp_file)
