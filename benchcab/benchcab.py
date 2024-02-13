# Copyright 2022 ACCESS-NRI and contributors. See the top-level COPYRIGHT file for details.
# SPDX-License-Identifier: Apache-2.0

"""Contains the benchcab application class."""

import grp
import os
import sys
from pathlib import Path
from subprocess import CalledProcessError
from typing import Optional

from benchcab import internal
from benchcab.comparison import run_comparisons, run_comparisons_in_parallel
from benchcab.config import read_config
from benchcab.environment_modules import EnvironmentModules, EnvironmentModulesInterface
from benchcab.fluxsite import (
    Task,
    get_fluxsite_comparisons,
    get_fluxsite_tasks,
    run_tasks,
    run_tasks_in_parallel,
)
from benchcab.internal import get_met_forcing_file_names
from benchcab.model import Model
from benchcab.utils import get_logger
from benchcab.utils.fs import mkdir, next_path
from benchcab.utils.pbs import render_job_script
from benchcab.utils.repo import SVNRepo, create_repo
from benchcab.utils.subprocess import SubprocessWrapper, SubprocessWrapperInterface
from benchcab.workdir import setup_fluxsite_directory_tree


class Benchcab:
    """A class that represents the `benchcab` application."""

    subprocess_handler: SubprocessWrapperInterface = SubprocessWrapper()
    modules_handler: EnvironmentModulesInterface = EnvironmentModules()

    def __init__(
        self,
        benchcab_exe_path: Optional[Path],
        validate_env: bool = True,
    ) -> None:
        """Constructor.

        Parameters
        ----------
        benchcab_exe_path : Optional[Path]
            Path to the executable.
        validate_env : bool, optional
            Validate the environment, by default True
        """
        self.benchcab_exe_path = benchcab_exe_path
        self.validate_env = validate_env

        self._config: Optional[dict] = None
        self._models: list[Model] = []
        self.tasks: list[Task] = []  # initialise fluxsite tasks lazily

        # Get the logger object
        self.logger = get_logger()

    def _validate_environment(self, project: str, modules: list):
        """Performs checks on current user environment."""
        if not self.validate_env:
            return

        if "gadi.nci" not in internal.NODENAME:
            self.logger.error("benchcab is currently implemented only on Gadi")
            sys.exit(1)

        namelist_dir = Path(internal.CWD / internal.NAMELIST_DIR)
        if not namelist_dir.exists():
            self.logger.error(
                "Cannot find 'namelists' directory in current working directory"
            )
            sys.exit(1)

        if project is None:
            msg = """Couldn't resolve project: check 'project' in config.yaml
                and/or $PROJECT set in ~/.config/gadi-login.conf
                """
            raise AttributeError(msg)

        required_groups = set([project, "ks32", "hh5"])
        groups = [grp.getgrgid(gid).gr_name for gid in os.getgroups()]
        if not required_groups.issubset(groups):
            msg = (
                f"""Error: user does not have the required group permissions.,
                The required groups are:,
                {", ".join(required_groups)}""",
            )
            raise PermissionError(msg)

        for modname in modules:
            if not self.modules_handler.module_is_avail(modname):
                self.logger.error(f"Module ({modname}) is not available.")
                sys.exit(1)

        all_site_ids = set(
            internal.MEORG_EXPERIMENTS["five-site-test"]
            + internal.MEORG_EXPERIMENTS["forty-two-site-test"]
        )
        for site_id in all_site_ids:
            paths = list(internal.MET_DIR.glob(f"{site_id}*"))
            if not paths:
                self.logger.error(
                    [
                        f"Failed to infer met file for site id '{site_id}' in "
                        f"{internal.MET_DIR}."
                    ]
                )
                sys.exit(1)
            if len(paths) > 1:
                self.logger.error(
                    f"Multiple paths infered for site id: '{site_id}' in {internal.MET_DIR}."
                )
                sys.exit(1)

    def _get_config(self, config_path: str) -> dict:
        if not self._config:
            self._config = read_config(config_path)
        return self._config

    def _get_models(self, config: dict) -> list[Model]:
        if not self._models:
            for id, sub_config in enumerate(config["realisations"]):
                repo = create_repo(
                    spec=sub_config.pop("repo"),
                    path=internal.SRC_DIR
                    / (sub_config["name"] if sub_config["name"] else Path()),
                )
                self._models.append(Model(repo=repo, model_id=id, **sub_config))
        return self._models

    def _initialise_tasks(self, config: dict) -> list[Task]:
        """A helper method that initialises and returns the `tasks` attribute."""
        self.tasks = get_fluxsite_tasks(
            models=self._get_models(config),
            science_configurations=config["science_configurations"],
            fluxsite_forcing_file_names=get_met_forcing_file_names(
                config["fluxsite"]["experiment"]
            ),
        )
        return self.tasks

    def validate_config(self, config_path: str):
        """Endpoint for `benchcab validate_config`."""
        _ = self._get_config(config_path)

    def fluxsite_submit_job(self, config_path: str, skip: list[str]) -> None:
        """Submits the PBS job script step in the fluxsite test workflow."""
        config = self._get_config(config_path)
        self._validate_environment(project=config["project"], modules=config["modules"])
        if self.benchcab_exe_path is None:
            msg = "Path to benchcab executable is undefined."
            raise RuntimeError(msg)

        job_script_path = Path(internal.QSUB_FNAME)
        self.logger.info(
            "Creating PBS job script to run fluxsite tasks on compute nodes"
        )

        self.logger.info(f"job_script_path = {job_script_path}")

        with job_script_path.open("w", encoding="utf-8") as file:
            contents = render_job_script(
                project=config["project"],
                config_path=config_path,
                modules=config["modules"],
                pbs_config=config["fluxsite"]["pbs"],
                skip_bitwise_cmp="fluxsite-bitwise-cmp" in skip,
                benchcab_path=str(self.benchcab_exe_path),
            )
            file.write(contents)

        try:
            proc = self.subprocess_handler.run_cmd(
                f"qsub {job_script_path}",
                capture_output=True,
            )
        except CalledProcessError as exc:
            self.logger.error("when submitting job to NCI queue, details to follow")
            self.logger.error(exc.output)
            raise

        self.logger.info(f"PBS job submitted: {proc.stdout.strip()}")
        self.logger.info("CABLE log file for each task is written to:")
        self.logger.info(f"{internal.FLUXSITE_DIRS['LOG']}/<task_name>_log.txt")
        self.logger.info("The CABLE standard output for each task is written to:")
        self.logger.info(f"{internal.FLUXSITE_DIRS['TASKS']}/<task_name>/out.txt")
        self.logger.info("The NetCDF output for each task is written to:")
        self.logger.info(f"{internal.FLUXSITE_DIRS['OUTPUT']}/<task_name>_out.nc")

    def checkout(self, config_path: str):
        """Endpoint for `benchcab checkout`."""
        config = self._get_config(config_path)
        self._validate_environment(project=config["project"], modules=config["modules"])

        mkdir(internal.SRC_DIR, exist_ok=True)

        self.logger.info("Checking out repositories...")
        rev_number_log = ""

        for model in self._get_models(config):
            model.repo.checkout()
            rev_number_log += f"{model.name}: {model.repo.get_revision()}\n"

        rev_number_log_path = next_path("rev_number-*.log")
        self.logger.info(f"Writing revision number info to {rev_number_log_path}")
        with rev_number_log_path.open("w", encoding="utf-8") as file:
            file.write(rev_number_log)

    def build(self, config_path: str):
        """Endpoint for `benchcab build`."""
        config = self._get_config(config_path)
        self._validate_environment(project=config["project"], modules=config["modules"])

        for repo in self._get_models(config):
            if repo.build_script:

                self.logger.info("Compiling CABLE using custom build script for")
                self.logger.info(f"realisation {repo.name}")
                repo.custom_build(modules=config["modules"])

            else:
                build_mode = "with MPI" if internal.MPI else "serially"
                self.logger.info(
                    f"Compiling CABLE {build_mode} for realisation {repo.name}..."
                )
                repo.pre_build()
                repo.run_build(modules=config["modules"])
                repo.post_build()
            self.logger.info(f"Successfully compiled CABLE for realisation {repo.name}")

    def fluxsite_setup_work_directory(self, config_path: str):
        """Endpoint for `benchcab fluxsite-setup-work-dir`."""
        config = self._get_config(config_path)
        self._validate_environment(project=config["project"], modules=config["modules"])

        tasks = self.tasks if self.tasks else self._initialise_tasks(config)
        self.logger.info("Setting up run directory tree for fluxsite tests...")
        setup_fluxsite_directory_tree()
        self.logger.info("Setting up tasks...")
        for task in tasks:
            task.setup_task()
        self.logger.info("Successfully setup fluxsite tasks")

    def fluxsite_run_tasks(self, config_path: str):
        """Endpoint for `benchcab fluxsite-run-tasks`."""
        config = self._get_config(config_path)
        self._validate_environment(project=config["project"], modules=config["modules"])

        tasks = self.tasks if self.tasks else self._initialise_tasks(config)
        self.logger.debug("Running fluxsite tasks...")
        try:
            multiprocess = config["fluxsite"]["multiprocess"]
        except KeyError:
            multiprocess = internal.FLUXSITE_DEFAULT_MULTIPROCESS
        if multiprocess:
            ncpus = config.get("pbs", {}).get(
                "ncpus", internal.FLUXSITE_DEFAULT_PBS["ncpus"]
            )
            run_tasks_in_parallel(tasks, n_processes=ncpus, verbose=verbose)
        else:
            run_tasks(tasks)
        self.logger.info("Successfully ran fluxsite tasks")

    def fluxsite_bitwise_cmp(self, config_path: str):
        """Endpoint for `benchcab fluxsite-bitwise-cmp`."""
        config = self._get_config(config_path)
        self._validate_environment(project=config["project"], modules=config["modules"])

        if not self.modules_handler.module_is_loaded("nccmp/1.8.5.0"):
            self.modules_handler.module_load(
                "nccmp/1.8.5.0"
            )  # use `nccmp -df` for bitwise comparisons

        tasks = self.tasks if self.tasks else self._initialise_tasks(config)
        comparisons = get_fluxsite_comparisons(tasks)

        self.logger.debug("Running comparison tasks...")
        try:
            multiprocess = config["fluxsite"]["multiprocess"]
        except KeyError:
            multiprocess = internal.FLUXSITE_DEFAULT_MULTIPROCESS
        if multiprocess:
            try:
                ncpus = config["fluxsite"]["pbs"]["ncpus"]
            except KeyError:
                ncpus = internal.FLUXSITE_DEFAULT_PBS["ncpus"]
            run_comparisons_in_parallel(comparisons, n_processes=ncpus, verbose=verbose)
        else:
            run_comparisons(comparisons)
        self.logger.info("Successfully ran comparison tasks")

    def fluxsite(self, config_path: str, no_submit: bool, skip: list[str]):
        """Endpoint for `benchcab fluxsite`."""
        self.checkout(config_path)
        self.build(config_path)
        self.fluxsite_setup_work_directory(config_path)
        if no_submit:
            self.fluxsite_run_tasks(config_path)
            if "fluxsite-bitwise-cmp" not in skip:
                self.fluxsite_bitwise_cmp(config_path)
        else:
            self.fluxsite_submit_job(config_path, skip)

    def spatial(self, config_path: str):
        """Endpoint for `benchcab spatial`."""

    def run(self, config_path: str, no_submit: bool, skip: list[str]):
        """Endpoint for `benchcab run`."""
        self.fluxsite(config_path, no_submit, skip)
        self.spatial(config_path)
