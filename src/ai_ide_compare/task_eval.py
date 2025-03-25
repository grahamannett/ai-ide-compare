"""Codebase metrics analyzer with modular architecture."""

import argparse
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Generator, Set

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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

    def analyze_file(self, file_path: Path) -> dict:
        """Analyze a single file and return its metrics."""
        try:
            with file_path.open("r", encoding="utf-8") as f:
                lines = sum(1 for _ in f)
        except UnicodeDecodeError:
            logger.warning(f"Skipping binary file: {file_path}")
            return None
        except Exception as e:
            logger.error(f"Error reading {file_path}: {str(e)}")
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


def eval_entrypoint():
    """Command-line interface for the analyzer."""
    parser = argparse.ArgumentParser(description="Codebase Metrics Analyzer")
    parser.add_argument("directory", help="Path to codebase directory")
    parser.add_argument("-o", "--output", help="Output file path (JSON format)")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    analyzer = CodebaseAnalyzer()
    try:
        metrics = analyzer.analyze(args.directory)
    except ValueError as e:
        logger.error(str(e))
        exit(1)

    result = {
        "total_files": metrics.total_files,
        "total_lines": metrics.total_lines,
        "files_by_type": metrics.files_by_type,
        "file_details": metrics.file_details,
        "ignored_files_count": len(metrics.ignored_files),
    }

    if args.output:
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2)
        logger.info(f"Results saved to {args.output}")
    else:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    eval_entrypoint()
