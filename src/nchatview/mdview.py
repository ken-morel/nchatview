from rich.console import Console
from rich.markdown import Markdown


def view_file(path: str):
    with open(path) as f:
        md = f.read()
        console = Console()
        md = Markdown(md)
        console.print(md)
