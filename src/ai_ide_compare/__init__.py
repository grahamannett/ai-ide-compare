import shutil
import sys

from ai_ide_compare import console
from ai_ide_compare.shared import DIRS
from ai_ide_compare.task_eval import eval_entrypoint
from ai_ide_compare.task_init import init_entrypoint

__all__ = ["eval_entrypoint", "init_entrypoint"]


def cleanup_task_results(not_dry_run: bool = True):
    """Cleanup results directory."""
    console.info(f"is not-dry-run: {not_dry_run=}")
    if DIRS.TASK_RESULTS.exists():
        for task_dir in DIRS.TASK_RESULTS.iterdir():
            console.info(f"Removing {task_dir}")
            if not_dry_run:
                shutil.rmtree(task_dir)


cmds = {
    "eval": eval_entrypoint,
    "init": init_entrypoint,
    "cleanup": cleanup_task_results,
}


def main():
    # eval_entrypoint()
    cleanup_task_results(not_dry_run="--not-dry-run" in set(sys.argv))
