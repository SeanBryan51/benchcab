#!/usr/bin/env python

"""Contains the main program entry point for `benchcab`."""

import sys

from benchcab.job_script import create_job_script, submit_job
from benchcab.bench_config import read_config
from benchcab.benchtree import setup_fluxnet_directory_tree, setup_src_dir
from benchcab.build_cable import build_cable
from benchcab.get_cable import (
    checkout_cable,
    checkout_cable_auxiliary,
    archive_rev_number,
)
from benchcab.internal import (
    validate_environment,
    get_met_sites,
    MULTIPROCESS,
    SITE_LOG_DIR,
    SITE_TASKS_DIR,
    SITE_OUTPUT_DIR,
)
from benchcab.task import get_fluxnet_tasks, Task
from benchcab.cli import generate_parser
from benchcab.run_cable_site import run_tasks, run_tasks_in_parallel


class Benchcab:
    """A class that represents the `benchcab` application."""

    def __init__(self) -> None:
        self.args = generate_parser().parse_args(
            sys.argv[1:] if sys.argv[1:] else ["-h"]
        )
        self.config = read_config(self.args.config)
        self.tasks: list[Task] = []  # initialise fluxnet tasks lazily
        validate_environment(
            project=self.config["project"], modules=self.config["modules"]
        )

    def _initialise_tasks(self) -> list[Task]:
        """A helper method that initialises and returns the `tasks` attribute."""
        self.tasks = get_fluxnet_tasks(
            realisations=self.config["realisations"],
            science_configurations=self.config["science_configurations"],
            met_sites=get_met_sites(self.config["experiment"]),
        )
        return self.tasks

    def checkout(self):
        """Endpoint for `benchcab checkout`."""
        setup_src_dir()
        print("Checking out repositories...")
        for branch in self.config["realisations"]:
            checkout_cable(branch, self.config["user"], verbose=self.args.verbose)
        checkout_cable_auxiliary(self.args.verbose)
        archive_rev_number()
        return self

    def build(self):
        """Endpoint for `benchcab build`."""
        for branch in self.config["realisations"]:
            build_cable(
                branch["build_script"],
                branch["name"],
                self.config["modules"],
                verbose=self.args.verbose,
            )
        return self

    def fluxnet_setup_work_directory(self):
        """Endpoint for `benchcab fluxnet-setup-work-dir`."""
        tasks = self.tasks if self.tasks else self._initialise_tasks()
        print("Setting up run directory tree for FLUXNET tests...")
        setup_fluxnet_directory_tree(fluxnet_tasks=tasks, verbose=self.args.verbose)
        print("Setting up tasks...")
        for task in tasks:
            task.setup_task(verbose=self.args.verbose)
        print("Successfully setup FLUXNET tasks")
        return self

    def fluxnet_run_tasks(self):
        """Endpoint for `benchcab fluxnet-run-tasks`."""
        if self.args.no_submit:
            tasks = self.tasks if self.tasks else self._initialise_tasks()
            print("Running FLUXNET tasks...")
            if MULTIPROCESS:
                run_tasks_in_parallel(tasks, self.args.verbose)
            else:
                run_tasks(tasks, self.args.verbose)
            print("Successfully ran FLUXNET tasks")
        else:
            create_job_script(
                project=self.config["project"],
                user=self.config["user"],
                config_path=self.args.config,
                modules=self.config["modules"],
                verbose=self.args.verbose,
            )
            submit_job()
            print(
                "The CABLE log file for each task is written to "
                f"{SITE_LOG_DIR}/<task_name>_log.txt"
            )
            print(
                "The CABLE standard output for each task is written to "
                f"{SITE_TASKS_DIR}/<task_name>/out.txt"
            )
            print(
                "The NetCDF output for each task is written to "
                f"{SITE_OUTPUT_DIR}/<task_name>_out.nc"
            )
        return self

    def fluxnet(self):
        """Endpoint for `benchcab fluxnet`."""
        self.checkout()
        self.build()
        self.fluxnet_setup_work_directory()
        self.fluxnet_run_tasks()
        return self

    def spatial(self):
        """Endpoint for `benchcab spatial`."""
        return self

    def run(self):
        """Endpoint for `benchcab run`."""
        self.fluxnet()
        self.spatial()
        return self

    def main(self):
        """Main function for `benchcab`."""

        if self.args.subcommand == "run":
            self.run()

        if self.args.subcommand == "checkout":
            self.checkout()

        if self.args.subcommand == "build":
            self.build()

        if self.args.subcommand == "fluxnet":
            self.fluxnet()

        if self.args.subcommand == "fluxnet-setup-work-dir":
            self.fluxnet_setup_work_directory()

        if self.args.subcommand == "fluxnet-run-tasks":
            self.fluxnet_run_tasks()

        if self.args.subcommand == "spatial":
            self.spatial()


def main():
    """Main program entry point for `benchcab`.

    This is required for setup.py entry_points
    """

    app = Benchcab()
    app.main()


if __name__ == "__main__":
    main()
