from rich.console import Console


console = Console()


def error(message: str):
    """Prints an error message to the console."""
    console.print(f"[bold red]Error:[/bold red] {message}")


def print(*args, **kwargs):
    """Prints arguments to the console using Rich."""
    console.print(*args, **kwargs)


def warn(message: str):
    """Prints a warning message to the console."""
    console.print(f"[yellow]Warn:[/yellow] {message}")


def info(message: str):
    """Prints an informational message to the console."""
    console.print(f"[blue]Info:[/blue] {message}")
