import warnings
import os
import subprocess
import typer
from typing import Optional
import uuid
from al.vectordb import NoteStore
from pyfzf.pyfzf import FzfPrompt
import tempfile
from pathlib import Path

from langchain.docstore.document import Document
from langchain_community.vectorstores.redis import RedisText, RedisNum, RedisTag
from langchain_community.vectorstores.redis import RedisFilter


app = typer.Typer(no_args_is_help=True)


vectorstore = NoteStore()


@app.command()
def add():
    modify_note("")


@app.command()
def search(query: Optional[list[str]] = typer.Argument(None, help="query text")):
    if not query:
        query = [""]
    query = " ".join(query)
    try:
        while True:
            results = vectorstore.search(query=query)

            if not results:
                typer.echo("No results found.")
                return

            fzf = FzfPrompt()

            temp_dir = tempfile.mkdtemp()
            temp_files = []
            for doc in results:
                temp_file = Path(temp_dir) / f"{doc[0].metadata.get('id')}.md"
                temp_file.write_text(doc[0].page_content)
                temp_files.append(str(temp_file))

            fzf_input = []
            for i, doc in enumerate(results):
                formatted_score = f"{doc[1]:.3f}"
                content = doc[0].page_content.replace("\n", "\\n")
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
                modify_note(content=selected_content, id=id)
            else:
                return
    except KeyboardInterrupt:
        return


def modify_note(content: str, id: Optional[str] = None):
    metadata = {}
    if id:
        temp_id = id.split(":")[-1]
        metadata["id"] = id
    else:
        temp_id = str(uuid.uuid4())

    editor = os.getenv("EDITOR", "vi")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file = Path(temp_dir) / f"{temp_id}.md"

        with open(temp_file, "w") as f:
            f.write(content)

        if content:
            subprocess.run([editor, temp_file])
        else:
            subprocess.run([editor, "+startinsert", temp_file])

        with open(temp_file, "r") as file:
            new_content = file.read()

    if new_content == content:
        return

    metadata["tags"] = [tag for tag in new_content.split() if tag.startswith("#")]
    metadata["contexts"] = [
        context for context in new_content.split() if context.startswith("@")
    ]
    metadata["projects"] = [
        project for project in new_content.split() if project.startswith("+")
    ]

    document = Document(page_content=new_content, metadata=metadata)

    if id and document.page_content == "":
        print(f"deleting document={id}")
        vectorstore.delete_document(document=document)
        return

    if id and len(document.page_content) != "":
        with warnings.catch_warnings(action="ignore"):
            vectorstore.delete_document(document=document)
            result = vectorstore.add_note(document.page_content)
        print(f"document moved: {id} => {result.note_id}")
        return

    with warnings.catch_warnings(action="ignore"):
        warnings.simplefilter("ignore")
        result = vectorstore.add_note(document.page_content)

    print(f"document added: {result.note_id}")
