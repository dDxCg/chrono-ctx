from pathlib import Path
from typing import Annotated
import typer

from vcs.services.configure import add_sources, remove_sources, health_check
from vcs.services.audit import get_sources, rollback_source, get_version_list, check_diff

cli = typer.Typer(name = "ctx")
sources_cli = typer.Typer()

cli.add_typer(sources_cli, name="source")

#Path completion
def complete_path(incomplete: str):
    p = Path(incomplete or ".")
    parent = p.parent if p.parent != Path("") else Path(".")

    for child in parent.iterdir():
        if child.name.startswith(p.name):
            yield str(child)

PathArg = typer.Argument(..., shell_complete=complete_path)

#Health check
@cli.command("health")
def health():
    health_check()

#Configuration
@sources_cli.command("add")
def sources_add(paths: list[Path] = PathArg):
    add_sources(paths)

@sources_cli.command("remove")
def sources_remove(paths: list[Path] = PathArg):
    remove_sources(paths)

@sources_cli.command("list")
def sources():
    get_sources()

#Audit
@cli.command("history")
def get_version_history(path: Path = PathArg):
    get_version_list(path)

@cli.command("rollback")
def rollback(
    path: Path = PathArg,
    version: Annotated[
        int,
        typer.Option("--version", "-v", help="Rollback version"),
    ] = 1,
):
    rollback_source(path, version)

@cli.command("diff")
def show_diff(
    path: Path = PathArg,
    from_version: Annotated[
        int | None,
        typer.Option("--from", help="Rollback version"),
    ] = None,
    to_version: Annotated[
        int | None,
        typer.Option("--to", help="Rollback version"),
    ] = None,
):
    check_diff(path, from_version, to_version)


if __name__ == "__main__":
    cli(prog_name="ctx")