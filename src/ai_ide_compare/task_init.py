import argparse
import datetime
import json
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional

from rich.panel import Panel
from rich.table import Table

from ai_ide_compare import console
from ai_ide_compare.shared import DIRS


@dataclass
class TaskMetadata:
    """Metadata for a task run."""

    # 'greenfield'/'brownfield'
    task_type: str
    # 'todo-app', 'snakegame'
    task_name: str
    # 'cursor', 'vscode/copilot'
    ide: str
    # {provider and model}
    llm: str
    # Optional fields must come after required fields
    ide_version: Optional[str] = None
    start_time: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    environment_info: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    notes: str = ""


def _get_templates(typ: str) -> dict[str, tuple[str, str]]:
    return {t.name: (str(t), typ) for t in (DIRS.TASKS / typ).iterdir() if t.is_dir()}


def save_metadata(metadata: TaskMetadata, output_dir: Path) -> Path:
    """Save metadata to the output directory."""
    metadata_path = output_dir / "metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(asdict(metadata), f, indent=2)
    return metadata_path


def detect_task_type(task_name: str) -> str:
    """Detect task type based on task name."""
    if (DIRS.TASKS / "greenfield" / task_name).exists():
        return "greenfield"
    elif (DIRS.TASKS / "brownfield" / task_name).exists():
        return "brownfield"
    else:
        console.error(f"Task '{task_name}' not found.")
        sys.exit(1)


def copy_task_template(
    output_dir: Path,
    task_template_dir: Path | str | None = None,
    task_type: str | None = None,
    task_name: str | None = None,
    **kwargs,
) -> None:
    """
    Copy task template files to the output directory.

    For copying files that are model specific, not sure if i will want to include some way to exclude?
    """

    def _template_dir(_type, _name):
        return DIRS.TASKS / _type / _name

    if isinstance(task_template_dir, str):
        template_dir = Path(task_template_dir)
    elif isinstance(task_template_dir, Path):
        template_dir = task_template_dir
    else:
        template_dir = _template_dir(task_type, task_name)

    if not template_dir.exists():
        console.error(f"Task template not found: {template_dir}")
        sys.exit(1)

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Copy all files and directories
    for item in template_dir.glob("*"):
        if item.is_file():
            shutil.copy2(item, output_dir / item.name)
        elif item.is_dir():
            shutil.copytree(item, output_dir / item.name)


def generate_output_path(metadata: TaskMetadata) -> Path:
    """Generate output path based on metadata."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create a clean directory name
    dir_name = f"{metadata.task_name}-{metadata.ide}-{metadata.llm}-{timestamp}"

    # Replace spaces and special characters
    dir_name = dir_name.replace(" ", "-").lower()

    return DIRS.TASK_RESULTS / dir_name


def get_ide_version(ide: str) -> Optional[str]:
    """Get IDE version using mise run version:<ide> command."""
    try:
        result = subprocess.run(
            ["mise", "run", f"version:{ide}"],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            version_output = result.stdout.strip()

            # If multiple lines are returned, take the first one as the version number
            if version_output:
                version_lines = [
                    line
                    for line in version_output.splitlines()
                    if line and not line.startswith("[version:")
                ]

                if version_lines:
                    return version_lines[0].strip()

        console.warn(f"Could not detect {ide=} version automatically.")
        return None
    except Exception as e:
        console.warn(f"Error detecting {ide=} version: {str(e)}")
        return None


def start_ide(ide: str, output_dir: Path):
    """Start the IDE."""
    subprocess.run(["mise", "run", f"ide:{ide}", output_dir])


def collect_environment_info() -> dict[str, Any]:
    """Collect information about the environment."""
    return {
        "platform": sys.platform,
        "python_version": sys.version.split()[0],
        "os_name": os.name,
        "machine": platform.machine(),
        "processor": platform.processor(),
        "system": platform.system(),
        "release": platform.release(),
    }


def print_task_info(metadata: TaskMetadata, output_dir: Path) -> None:
    """Print task information in a rich table."""
    console.print(Panel.fit("[bold blue]Task Initialized[/bold blue]"))

    table = Table(show_header=False)
    table.add_column("Property", style="bold")
    table.add_column("Value")

    table.add_row("Task Type", metadata.task_type)
    table.add_row("Task Name", metadata.task_name)
    table.add_row("IDE", f"{metadata.ide} {metadata.ide_version or ''}")
    table.add_row("LLM", metadata.llm)
    table.add_row("Output Directory", str(output_dir))
    table.add_row("Start Time", metadata.start_time)

    console.print(table)

    console.print("\n[green]Task files copied and ready for development![/green]")
    console.print(
        f"[bold]Next steps:[/bold] Navigate to [blue]{output_dir}[/blue] to start working on the task."
    )


def init_entrypoint():
    """Entry point for task initialization."""
    parser = argparse.ArgumentParser(
        description="Initialize a new AI IDE comparison task"
    )
    parser.add_argument(
        "task_name", help="Name of the task (e.g., todo-app, snakegame)"
    )
    parser.add_argument("ide", help="IDE name (e.g., vscode, cursor, copilot)")
    parser.add_argument("llm", help="LLM model (e.g., anthropic-claude3.7, gpt-4)")

    parser.add_argument(
        "--task-type",
        choices=["greenfield", "brownfield"],
        help="Type of task (will auto-detect if not provided)",
    )
    parser.add_argument("--tags", nargs="+", help="Tags for categorizing this task run")
    parser.add_argument("--notes", help="Additional notes about this task run")
    parser.add_argument("--output-dir", help="Custom output directory")
    parser.add_argument("--start-ide", help="Start the IDE", action="store_true")

    args = parser.parse_args()

    task_templates = {
        **_get_templates("greenfield"),
        **_get_templates("brownfield"),
    }

    task_template_dir, task_type = task_templates[args.task_name]

    console.print(f"[blue]Detecting {args.ide} version...[/blue]")
    ide_version = get_ide_version(args.ide)
    if ide_version:
        console.print(f"[green]Detected {args.ide} version:[/green] {ide_version}")

    console.print("[blue]Collecting env info...[/blue]")
    env_info = collect_environment_info()

    metadata = TaskMetadata(
        task_type=task_type,
        task_name=args.task_name,
        ide=args.ide,
        llm=args.llm,
        ide_version=ide_version,
        tags=args.tags or [],
        notes=args.notes or "",
        environment_info=env_info,
    )

    # Generate output path
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = generate_output_path(metadata)

    # result directory
    console.print(f"[bold blue]Init task:[/bold blue] {task_type}/{args.task_name}")
    console.print(f"[bold blue]Output dir:[/bold blue] {output_dir}")

    # Copy task template

    copy_task_template(output_dir=output_dir, task_template_dir=task_template_dir)

    save_metadata(metadata, output_dir)
    print_task_info(metadata, output_dir)

    if args.start_ide:
        start_ide(args.ide, output_dir)


if __name__ == "__main__":
    init_entrypoint()
