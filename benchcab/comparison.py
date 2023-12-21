# Copyright 2022 ACCESS-NRI and contributors. See the top-level COPYRIGHT file for details.
# SPDX-License-Identifier: Apache-2.0

"""A module containing functions and data structures for running comparison tasks."""

import multiprocessing
import operator
import sys
from pathlib import Path
from subprocess import CalledProcessError

from benchcab import internal
from benchcab.utils.subprocess import SubprocessWrapper, SubprocessWrapperInterface


class ComparisonTask:
    """A class used to represent a single bitwise comparison task."""

    subprocess_handler: SubprocessWrapperInterface = SubprocessWrapper()

    def __init__(
        self,
        files: tuple[Path, Path],
        task_name: str,
    ) -> None:
        """Constructor.

        Parameters
        ----------
        files : tuple[Path, Path]
            Files.
        task_name : str
            Name of the task.
        """
        self.files = files
        self.task_name = task_name

    def run(self, verbose=False) -> None:
        """Executes `nccmp -df` on the NetCDF files pointed to by `self.files`."""
        file_a, file_b = self.files
        if verbose:
            print(f"Comparing files {file_a.name} and {file_b.name} bitwise...")

        try:
            self.subprocess_handler.run_cmd(
                f"nccmp -df {file_a} {file_b}",
                capture_output=True,
                verbose=verbose,
            )
            print(f"Success: files {file_a.name} {file_b.name} are identical")
        except CalledProcessError as exc:
            output_file = (
                internal.FLUXSITE_DIRS["BITWISE_CMP"] / f"{self.task_name}.txt"
            )
            with output_file.open("w", encoding="utf-8") as file:
                file.write(exc.stdout)
            print(
                f"Failure: files {file_a.name} {file_b.name} differ. "
                f"Results of diff have been written to {output_file}"
            )
        sys.stdout.flush()


def run_comparisons(comparison_tasks: list[ComparisonTask], verbose=False) -> None:
    """Runs bitwise comparison tasks serially."""
    for task in comparison_tasks:
        task.run(verbose=verbose)


def run_comparisons_in_parallel(
    comparison_tasks: list[ComparisonTask],
    n_processes=internal.FLUXSITE_DEFAULT_PBS["ncpus"],
    verbose=False,
) -> None:
    """Runs bitwise comparison tasks in parallel across multiple processes."""
    run_task = operator.methodcaller("run", verbose=verbose)
    with multiprocessing.Pool(n_processes) as pool:
        pool.map(run_task, comparison_tasks, chunksize=1)
