from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from myai.baseline import baseline_input_hash, build_baseline_request, run_baseline_result
from myai.fixtures import CompanyFixture, northstar_fixture
from myai.providers.anthropic import AnthropicStructuredModel
from myai.run_store import save_baseline_run
from myai.settings import Settings

app = typer.Typer(no_args_is_help=True, help="myAI modernization research CLI")
console = Console()

RootOption = Annotated[Path | None, typer.Option(exists=True, file_okay=False)]
EnvironmentArgument = Annotated[str, typer.Argument()]
ModelOption = Annotated[str, typer.Option(help="Anthropic model ID")]
RunsOption = Annotated[int, typer.Option(help="Number of paid baseline calls to execute")]


def _northstar(environment: str, repo_root: Path) -> CompanyFixture:
    if environment != "northstar":
        raise typer.BadParameter("only 'northstar' is available in v0.1")
    return northstar_fixture(repo_root)


@app.command()
def inspect(
    environment: EnvironmentArgument = "northstar",
    root: RootOption = None,
) -> None:
    """Inspect a controlled company fixture without invoking an LLM."""
    repo_root = root or Path.cwd()
    fixture = _northstar(environment, repo_root)
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
    repo_root = root or Path.cwd()
    fixture = _northstar(environment, repo_root)
    payload = {
        "company": fixture.company(),
        "evidence": [item.model_dump(mode="json") for item in fixture.evidence()],
    }
    console.print_json(json.dumps(payload))


@app.command()
def baseline(
    environment: EnvironmentArgument = "northstar",
    model: ModelOption = "claude-sonnet-5",
    runs: RunsOption = 1,
    root: RootOption = None,
) -> None:
    """Run the paid one-shot Anthropic baseline and persist immutable artifacts."""
    if runs < 1 or runs > 20:
        raise typer.BadParameter("--runs must be between 1 and 20")

    repo_root = root or Path.cwd()
    fixture = _northstar(environment, repo_root)
    evidence = fixture.evidence()
    known_evidence_ids = {item.id for item in evidence}

    try:
        api_key = Settings().require_anthropic_api_key()
    except RuntimeError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=2) from exc

    gateway = AnthropicStructuredModel(api_key)
    request = build_baseline_request(fixture, model)
    input_hash = baseline_input_hash(fixture, model)

    for run_number in range(1, runs + 1):
        console.print(f"\n[bold]Baseline run {run_number}/{runs}[/bold] — {model}")
        result = run_baseline_result(fixture, gateway, model)
        run_dir, metadata = save_baseline_run(
            repo_root=repo_root,
            environment=environment,
            request=request,
            result=result,
            input_hash=input_hash,
            known_evidence_ids=known_evidence_ids,
        )

        table = Table(title="Ranked modernization opportunities")
        table.add_column("Rank", justify="right")
        table.add_column("Opportunity")
        table.add_column("Value/yr", justify="right")
        table.add_column("Confidence", justify="right")
        table.add_column("Feasibility", justify="right")
        table.add_column("Evidence")
        for rank, opportunity in enumerate(result.value.opportunities, start=1):
            value = (
                f"${opportunity.annual_value_usd:,.0f}"
                if opportunity.annual_value_usd is not None
                else "—"
            )
            table.add_row(
                str(rank),
                opportunity.title,
                value,
                f"{opportunity.confidence:.0%}",
                f"{opportunity.feasibility:.0%}",
                ", ".join(str(item)[:8] for item in opportunity.evidence_ids),
            )
        console.print(table)

        cost = f"${metadata.cost_usd:.4f}" if metadata.cost_usd is not None else "unknown"
        console.print(
            f"Tokens: {metadata.input_tokens or 0:,} in / {metadata.output_tokens or 0:,} out | "
            f"Latency: {metadata.latency_ms or 0:,} ms | Estimated cost: {cost}"
        )
        if metadata.invalid_evidence_ids:
            console.print(
                f"[yellow]Invalid evidence citations: {len(metadata.invalid_evidence_ids)}[/yellow]"
            )
        else:
            console.print("Evidence citations: all IDs exist in the observable fixture")
        console.print(f"Artifacts: {run_dir}")


if __name__ == "__main__":
    app()
