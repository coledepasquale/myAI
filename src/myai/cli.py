from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from myai.fixtures import CompanyFixture, northstar_fixture

app = typer.Typer(no_args_is_help=True, help="myAI modernization research CLI")
console = Console()

RootOption = Annotated[Path | None, typer.Option(exists=True, file_okay=False)]
EnvironmentArgument = Annotated[str, typer.Argument()]


@app.command()
def inspect(
    environment: EnvironmentArgument = "northstar",
    root: RootOption = None,
) -> None:
    """Inspect a controlled company fixture without invoking an LLM."""
    if environment != "northstar":
        raise typer.BadParameter("only 'northstar' is available in v0.1")

    fixture: CompanyFixture = northstar_fixture(root or Path.cwd())
    company = fixture.company()
    evidence = fixture.evidence()

    console.print(f"[bold]{company['name']}[/bold]")
    console.print(f"Employees: {company['employee_count']}")
    console.print(f"Evidence items: {len(evidence)}")

    table = Table(title="Observable evidence")
    table.add_column("ID")
    table.add_column("Kind")
    table.add_column("Source")
    table.add_column("Excerpt")
    for item in evidence:
        table.add_row(str(item.id)[:8], item.kind.value, item.source, item.content[:90])
    console.print(table)


@app.command("dump-context")
def dump_context(
    environment: EnvironmentArgument = "northstar",
    root: RootOption = None,
) -> None:
    """Emit exactly the observable context used by baseline experiments."""
    if environment != "northstar":
        raise typer.BadParameter("only 'northstar' is available in v0.1")

    fixture = northstar_fixture(root or Path.cwd())
    payload = {
        "company": fixture.company(),
        "evidence": [item.model_dump(mode="json") for item in fixture.evidence()],
    }
    console.print_json(json.dumps(payload))


if __name__ == "__main__":
    app()
