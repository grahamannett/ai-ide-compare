"""Codebase metrics analyzer with modular architecture."""

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Generator, Set, Optional, Literal, Any

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint

# Initialize Rich console
console = Console()


_DEFAULT_IGNORE_PATTERNS = {
    "__pycache__",
    ".venv",
    "node_modules",
    ".git",
    ".mise.*.toml",
    "*.pyc",
    ".DS_Store",
    "*.swp",
    "*.env",
}


@dataclass
class CodebaseMetrics:
    """Dataclass to hold codebase metrics."""

    total_files: int = 0
    total_lines: int = 0
    files_by_type: dict[str, int] = field(default_factory=dict)
    file_details: list[dict] = field(default_factory=list)
    ignored_files: Set[Path] = field(default_factory=set)


class CodebaseAnalyzer:
    """Modular codebase analyzer with configurable ignore patterns."""

    def __init__(self, ignore_patterns: Set[str] | None = None):
        self.ignore_patterns = _DEFAULT_IGNORE_PATTERNS.copy()
        if ignore_patterns:
            self.ignore_patterns |= ignore_patterns

    def should_ignore(self, path: Path) -> bool:
        """Check if a path matches any ignore pattern."""
        return any(path.match(pattern) for pattern in self.ignore_patterns)

    def collect_files(self, directory: Path) -> Generator[Path, None, None]:
        """Generate all non-ignored files in the directory."""
        for path in directory.rglob("*"):
            if path.is_file() and not self.should_ignore(path):
                yield path

    def analyze_file(self, file_path: Path) -> Optional[dict[str, Any]]:
        """Analyze a single file and return its metrics."""
        try:
            with file_path.open("r", encoding="utf-8") as f:
                lines = sum(1 for _ in f)
        except UnicodeDecodeError:
            console.print(f"[yellow]Skipping binary file:[/yellow] {file_path}")
            return None
        except Exception as e:
            console.print(f"[red]Error reading {file_path}:[/red] {str(e)}")
            return None

        return {
            "path": str(file_path.relative_to(file_path.parent)),
            "lines": lines,
            "type": file_path.suffix.lower() or "no_extension",
        }

    def analyze(self, directory: str) -> CodebaseMetrics:
        """Analyze the entire codebase and return metrics."""
        base_path = Path(directory)
        metrics = CodebaseMetrics()

        with console.status("[bold green]Analyzing codebase...") as status:
            for file_path in self.collect_files(base_path):
                file_metrics = self.analyze_file(file_path)
                if not file_metrics:
                    metrics.ignored_files.add(file_path)
                    continue

                metrics.total_files += 1
                metrics.total_lines += file_metrics["lines"]
                file_type = file_metrics["type"]
                metrics.files_by_type[file_type] = (
                    metrics.files_by_type.get(file_type, 0) + 1
                )
                metrics.file_details.append(file_metrics)

        return metrics


def metrics_to_dict(metrics: CodebaseMetrics) -> dict[str, Any]:
    """Convert metrics to a dictionary."""
    return {
        "total_files": metrics.total_files,
        "total_lines": metrics.total_lines,
        "files_by_type": metrics.files_by_type,
        "file_details": metrics.file_details,
        "ignored_files_count": len(metrics.ignored_files),
    }


def metrics_to_markdown(metrics: CodebaseMetrics) -> str:
    """Convert metrics to a markdown string."""
    md = []
    md.append("# Codebase Analysis Results\n")

    md.append("## Summary\n")
    md.append(f"- Total Files: **{metrics.total_files}**")
    md.append(f"- Total Lines of Code: **{metrics.total_lines}**")
    md.append(f"- Ignored Files: **{len(metrics.ignored_files)}**\n")

    md.append("## Files by Type\n")
    md.append("| File Type | Count |")
    md.append("|-----------|-------|")
    for file_type, count in sorted(
        metrics.files_by_type.items(), key=lambda x: x[1], reverse=True
    ):
        md.append(f"| {file_type} | {count} |")

    md.append("\n## Top 10 Largest Files\n")
    md.append("| File | Lines |")
    md.append("|------|-------|")
    for file in sorted(metrics.file_details, key=lambda x: x["lines"], reverse=True)[
        :10
    ]:
        md.append(f"| {file['path']} | {file['lines']} |")

    return "\n".join(md)


def print_rich_output(metrics: CodebaseMetrics) -> None:
    """Display metrics in a rich console format."""
    console.print(Panel.fit("[bold blue]Codebase Analysis Results[/bold blue]"))

    # Summary
    console.print("[bold]Summary:[/bold]")
    console.print(f"Total Files: [bold green]{metrics.total_files}[/bold green]")
    console.print(
        f"Total Lines of Code: [bold green]{metrics.total_lines}[/bold green]"
    )
    console.print(
        f"Ignored Files: [bold yellow]{len(metrics.ignored_files)}[/bold yellow]"
    )

    # Files by Type
    console.print("\n[bold]Files by Type:[/bold]")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("File Type")
    table.add_column("Count", justify="right")

    for file_type, count in sorted(
        metrics.files_by_type.items(), key=lambda x: x[1], reverse=True
    ):
        table.add_row(file_type, str(count))

    console.print(table)

    # Top 10 Largest Files
    console.print("\n[bold]Top 10 Largest Files:[/bold]")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("File")
    table.add_column("Lines", justify="right")

    for file in sorted(metrics.file_details, key=lambda x: x["lines"], reverse=True)[
        :10
    ]:
        table.add_row(file["path"], str(file["lines"]))

    console.print(table)


def eval_entrypoint():
    import sys

    breakpoint()

    """Command-line interface for the analyzer."""
    parser = argparse.ArgumentParser(description="Codebase Metrics Analyzer")
    parser.add_argument("directory", help="Path to codebase directory")
    parser.add_argument("-o", "--output", help="Output file path")
    parser.add_argument(
        "-f",
        "--format",
        choices=["json", "markdown"],
        default="json",
        help="Output format (json or markdown)",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )

    args = parser.parse_args()

    console.print(f"[bold blue]Analyzing directory:[/bold blue] {args.directory}")

    if args.verbose:
        console.print("[yellow]Verbose mode enabled[/yellow]")

    analyzer = CodebaseAnalyzer()
    try:
        metrics = analyzer.analyze(args.directory)
    except ValueError as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        exit(1)

    # Display results in the terminal
    # print_rich_output(metrics)
    console.print(metrics_to_markdown(metrics))
    # console.log(metrics)

    # Save to file if specified
    if args.output:
        if args.format == "json":
            result = metrics_to_dict(metrics)
            with open(args.output, "w") as f:
                json.dump(result, f, indent=2)
        else:  # markdown
            result = metrics_to_markdown(metrics)
            with open(args.output, "w") as f:
                f.write(result)

        console.print(f"\n[green]Results saved to:[/green] {args.output}")


if __name__ == "__main__":
    eval_entrypoint()
