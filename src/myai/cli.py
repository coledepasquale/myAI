from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from myai.baseline import baseline_input_hash, build_baseline_request, run_baseline_result
from myai.benchmark import FilesystemPackLoader, default_pack_path
from myai.benchmark.generator import generate_pack, load_params
from myai.benchmark.loader import PACK_ENV_VAR
from myai.benchmark.runner import CaseOutcome, run_benchmark_suite
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
PackOption = Annotated[Path | None, typer.Option(help="Benchmark pack directory or file")]
AllowTrackedOption = Annotated[
    bool,
    typer.Option(help="Permit a Git-tracked pack. Only valid for the public toy/example pack."),
]


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

    settings = Settings()
    try:
        api_key = settings.require_anthropic_api_key()
    except RuntimeError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=2) from exc

    gateway = AnthropicStructuredModel(
        api_key,
        workspace_id=settings.optional_anthropic_workspace_id(),
    )
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


def _is_tracked_by_git(path: Path) -> bool:
    """True when Git tracks this file, which would make a private pack public."""
    try:
        completed = subprocess.run(
            ["git", "ls-files", "--error-unmatch", str(path)],
            capture_output=True,
            cwd=path.parent,
            check=False,
        )
    except OSError:
        return False
    return completed.returncode == 0


def _is_git_ignored(repo_root: Path, path: Path) -> bool | None:
    """True/False when Git can answer; None when the path is outside any repo."""
    try:
        completed = subprocess.run(
            ["git", "check-ignore", "-q", str(path)],
            capture_output=True,
            cwd=repo_root,
            check=False,
        )
    except OSError:
        return None
    if completed.returncode == 0:
        return True
    if completed.returncode == 1:
        return False
    return None


@app.command("benchmark-generate")
def benchmark_generate(
    params: Annotated[Path | None, typer.Option(help="Private generator params JSON")] = None,
    out: Annotated[Path | None, typer.Option(help="Output directory for pack + manifest")] = None,
    root: RootOption = None,
) -> None:
    """Generate a private Northstar benchmark pack from a private parameter file."""
    repo_root = root or Path.cwd()
    params_path = params or repo_root / "benchmarks" / "private" / "params.json"
    out_dir = out or repo_root / "benchmarks" / "private"

    if not params_path.is_file():
        console.print(
            f"[red]No parameter file at {params_path}.[/red]\n"
            "Copy benchmarks/params.example.json there, set a private seed, and adjust "
            "rates if desired."
        )
        raise typer.Exit(code=2)

    pack_file = out_dir / "pack.json"
    if _is_git_ignored(repo_root, pack_file) is False:
        console.print(
            f"[red]SECURITY: {pack_file} would not be git-ignored. Hidden answers must "
            "never be committed. Write the pack under benchmarks/private/ or outside "
            "the repository.[/red]"
        )
        raise typer.Exit(code=3)

    try:
        loaded_params = load_params(params_path.read_text())
        company = _northstar("northstar", repo_root).company()
        generated_pack, manifest = generate_pack(loaded_params, company)
    except (ValueError, RuntimeError) as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    out_dir.mkdir(parents=True, exist_ok=True)
    pack_file.write_text(generated_pack.model_dump_json(indent=2) + "\n")
    (out_dir / "manifest.json").write_text(manifest.model_dump_json(indent=2) + "\n")

    console.print(f"[bold]Pack {generated_pack.pack_version}[/bold] written to {pack_file}")
    console.print(
        f"Cases: {len(generated_pack.cases)} | "
        f"Categories: {len(generated_pack.category_rules)}"
    )
    console.print(f"Pack hash: [bold]{generated_pack.pack_hash}[/bold]")
    console.print(
        "manifest.json beside the pack contains the answers and per-case arithmetic "
        "for your private review. Never paste either file into a chat or commit."
    )
    console.print(
        "Next: spot-check a few cases in manifest.json, run [bold]myai "
        "benchmark-validate[/bold], and record the pack hash to freeze the target."
    )


@app.command("benchmark-run")
def benchmark_run(
    model: ModelOption = "claude-sonnet-5",
    pack: PackOption = None,
    expect_hash: Annotated[
        str | None,
        typer.Option(help="Abort unless the loaded pack has exactly this hash"),
    ] = None,
    limit: Annotated[
        int | None, typer.Option(help="Only run the first N cases (paid-call budget guard)")
    ] = None,
    repeat: Annotated[
        int, typer.Option(min=1, max=5, help="Paid runs per case (for stability measurement)")
    ] = 1,
    root: RootOption = None,
) -> None:
    """Run one model over every benchmark case, score against the private pack."""
    repo_root = root or Path.cwd()
    pack_path = pack or default_pack_path(repo_root)
    try:
        loaded = FilesystemPackLoader(pack_path).load()
    except (FileNotFoundError, ValueError) as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=2) from exc

    if expect_hash is not None and loaded.pack_hash != expect_hash:
        console.print(
            f"[red]Pack hash mismatch: expected {expect_hash}, loaded pack has "
            f"{loaded.pack_hash}. The frozen target and this pack are not the same "
            "artifact — refusing to run.[/red]"
        )
        raise typer.Exit(code=3)

    settings = Settings()
    try:
        api_key = settings.require_anthropic_api_key()
    except RuntimeError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=2) from exc
    gateway = AnthropicStructuredModel(
        api_key,
        workspace_id=settings.optional_anthropic_workspace_id(),
    )

    total = limit if limit is not None else len(loaded.cases)
    console.print(
        f"[bold]Benchmark suite[/bold] — {model} | pack {loaded.pack_version} "
        f"({loaded.pack_hash[:16]}…) | {total} cases x {repeat} run(s), paid"
    )

    def show(outcome: CaseOutcome) -> None:
        if outcome.run is not None:
            score = outcome.run.score
            cost = f"${outcome.run.cost_usd:.4f}" if outcome.run.cost_usd else "?"
            console.print(
                f"  {outcome.case_id}: top1={'HIT' if score.top1_correct else 'miss'} "
                f"recall@3={score.top3_recall:.2f} "
                f"invalid_ev={score.invalid_evidence_id_count} "
                f"violations={score.critical_policy_violations} {cost}"
            )
        else:
            console.print(f"  [red]{outcome.case_id}: FAILED — {outcome.error}[/red]")

    result = run_benchmark_suite(
        loaded, gateway, model,
        repo_root=repo_root, limit=limit, repeat=repeat, on_case=show,
    )

    report = result.report
    console.print(f"\n[bold]Report — {model} on {report.pack_version}[/bold]")
    table = Table(show_header=False)
    table.add_column("Metric")
    table.add_column("Value", justify="right")

    def fmt(value: float | None, pct: bool = False) -> str:
        if value is None:
            return "n/a"
        return f"{value:.0%}" if pct else f"{value:.3f}"

    table.add_row("Cases scored / attempted", f"{report.run_count}/{result.record.case_count}")
    table.add_row("Top-1 accuracy", fmt(report.top1_accuracy, pct=True))
    table.add_row("Top-3 recall", fmt(report.mean_top3_recall, pct=True))
    table.add_row("Rank correlation", fmt(report.mean_rank_correlation))
    table.add_row(
        "Evidence citation validity", fmt(report.mean_evidence_citation_validity, pct=True)
    )
    table.add_row("Invalid evidence IDs", str(report.total_invalid_evidence_ids))
    table.add_row("Decoy in top-3", fmt(report.mean_decoy_top3_rate, pct=True))
    table.add_row("Unsupported ROI rate", fmt(report.mean_unsupported_roi_rate, pct=True))
    table.add_row("ROI band coverage", fmt(report.mean_roi_band_coverage, pct=True))
    table.add_row("ROI calibration error", fmt(report.mean_roi_calibration_error))
    table.add_row("Policy detection", fmt(report.mean_policy_detection_rate, pct=True))
    table.add_row("Critical policy violations", str(report.total_critical_policy_violations))
    table.add_row("Confidence Brier", fmt(report.mean_confidence_calibration_error))
    table.add_row("Top-1 stability", fmt(report.top1_stability, pct=True))
    table.add_row("Tokens in/out", f"{report.total_input_tokens:,}/{report.total_output_tokens:,}")
    cost_text = f"${report.total_cost_usd:.4f}" if report.total_cost_usd is not None else "unknown"
    table.add_row("Estimated cost", cost_text)
    console.print(table)

    if result.record.failed_case_ids:
        console.print(
            f"[yellow]Failed cases (excluded from report): "
            f"{', '.join(result.record.failed_case_ids)}[/yellow]"
        )
    console.print(f"Artifacts: {result.run_dir}")


@app.command("benchmark-validate")
def benchmark_validate(
    pack: PackOption = None,
    root: RootOption = None,
    allow_tracked: AllowTrackedOption = False,
) -> None:
    """Validate a benchmark pack and summarize it without revealing any answers."""
    repo_root = root or Path.cwd()
    pack_path = pack or default_pack_path(repo_root)
    loader = FilesystemPackLoader(pack_path)

    try:
        loaded = loader.load()
    except FileNotFoundError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=2) from exc
    except ValueError as exc:
        console.print(f"[red]Benchmark pack is invalid:[/red]\n{exc}")
        raise typer.Exit(code=1) from exc

    if not allow_tracked and _is_tracked_by_git(loader.pack_file):
        console.print(
            f"[red]SECURITY: {loader.pack_file} is tracked by Git. "
            "Hidden benchmark answers must never be committed to a public repository. "
            f"Move the pack into benchmarks/private/ or point {PACK_ENV_VAR} elsewhere. "
            "Pass --allow-tracked only for the public toy/example pack.[/red]"
        )
        raise typer.Exit(code=3)

    console.print(f"[bold]Pack {loaded.pack_version}[/bold]")
    console.print(f"Source: {loader.pack_file}")
    console.print(f"Pack hash: {loaded.pack_hash}")
    console.print(f"Categories: {len(loaded.category_rules)}")

    table = Table(title="Observable benchmark cases (answers withheld)")
    table.add_column("Case")
    table.add_column("Variant")
    table.add_column("Evidence", justify="right")
    for case in loaded.observable_cases():
        table.add_row(case.case_id, case.variant_id, str(len(case.evidence)))
    console.print(table)
    console.print(
        f"[green]Pack is complete and internally consistent: "
        f"{len(loaded.cases)} cases[/green]"
    )


if __name__ == "__main__":
    app()
