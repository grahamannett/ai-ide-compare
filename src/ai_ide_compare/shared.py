from pathlib import Path


class DIRS:
    """Default paths for dirs as constants."""

    TASKS: Path = Path("tasks")
    RESULTS: Path = Path("results")
    TASK_RESULTS: Path = RESULTS / "tasks"


class IDES:
    CURSOR = "cursor"
    VSCODE = "code"  # need to account for 'code-insiders'/USEINSIDERS
    COPILOT = VSCODE

    WINDSURF = "windsurf"
