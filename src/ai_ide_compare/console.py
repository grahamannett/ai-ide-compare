from rich.console import Console
from typing import Optional
import os
import re


console = Console()

# Regex to strip ANSI color codes
ANSI_ESCAPE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


class OutputHandler:
    """Handles output to console and/or file."""

    log_file: Optional[str] = None
    capture_to_file: bool = False

    @classmethod
    def start_capture(cls, file_path: str):
        """Start capturing output to a file."""
        cls.log_file = file_path
        cls.capture_to_file = True
        # Create directory if needed
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        # Clear file if it exists
        with open(file_path, "w") as f:
            pass

    @classmethod
    def stop_capture(cls):
        """Stop capturing output to a file."""
        cls.capture_to_file = False


def _print(message: str) -> None:
    """Internal print function that handles file logging."""
    if OutputHandler.capture_to_file and OutputHandler.log_file:
        with open(OutputHandler.log_file, "a") as f:
            # Strip ANSI color codes for file output
            try:
                clean_msg = ANSI_ESCAPE.sub("", message)
            except Exception as e:
                f.write(f"Error stripping ANSI color codes: {e}")
                clean_msg = message
            f.write(f"{clean_msg}\n")

    # Always print to console unless we're capturing
    if not OutputHandler.capture_to_file:
        console.print(message)


def error(message: str):
    """Prints an error message to the console."""
    _print(f"[bold red]Error:[/bold red] {message}")


def print(*args, **kwargs):
    """Prints arguments to the console using Rich."""
    _print(*args, **kwargs)


def warn(message: str):
    """Prints a warning message to the console."""
    _print(f"[yellow]Warn:[/yellow] {message}")


def info(message: str):
    """Prints an informational message to the console."""
    _print(f"[blue]Info:[/blue] {message}")


def stdout(message: str):
    """Prints a message to stdout regardless of capture mode."""
    console.print(message)
