# Copyright 2022 ACCESS-NRI and contributors. See the top-level COPYRIGHT file for details.
# SPDX-License-Identifier: Apache-2.0

"""A module containing functions and data structures for running spatial tasks."""

from typing import Optional

import git
import yaml

from benchcab import internal
from benchcab.model import Model
from benchcab.utils.dict import deep_update
from benchcab.utils.fs import chdir
from benchcab.utils.namelist import patch_namelist, patch_remove_namelist
from benchcab.utils.subprocess import SubprocessWrapper, SubprocessWrapperInterface


class SpatialTask:
    """A class used to represent a single spatial task."""

    subprocess_handler: SubprocessWrapperInterface = SubprocessWrapper()

    def __init__(
        self,
        model: Model,
        met_forcing_name: str,
        met_forcing_payu_experiment: str,
        sci_conf_id: int,
        sci_config: dict,
        payu_args: Optional[str] = None,
    ) -> None:
        self.model = model
        self.met_forcing_name = met_forcing_name
        self.met_forcing_payu_experiment = met_forcing_payu_experiment
        self.sci_conf_id = sci_conf_id
        self.sci_config = sci_config
        self.payu_args = payu_args

    def get_task_name(self) -> str:
        """Returns the file name convention used for this task."""
        return f"{self.met_forcing_name}_R{self.model.model_id}_S{self.sci_conf_id}"

    def setup_task(self, payu_config: Optional[dict] = None, verbose=False):
        """Does all file manipulations to run cable with payu for this task."""

        if verbose:
            print(f"Setting up task: {self.get_task_name()}")

        self.clone_experiment(verbose=verbose)
        self.configure_experiment(payu_config, verbose=verbose)
        self.update_namelist(verbose=verbose)

    def clone_experiment(self, verbose=False):
        """Clone the payu experiment from GitHub."""
        url = self.met_forcing_payu_experiment
        path = internal.SPATIAL_TASKS_DIR / self.get_task_name()
        if verbose:
            print(f"git clone {url} {path}")
        _ = git.Repo.clone_from(url, path)

    def configure_experiment(self, payu_config: Optional[dict] = None, verbose=False):
        """Configure the payu experiment for this task."""
        task_dir = internal.SPATIAL_TASKS_DIR / self.get_task_name()
        exp_config_path = task_dir / "config.yaml"
        with exp_config_path.open("r", encoding="utf-8") as file:
            config = yaml.safe_load(file)
            if config is None:
                config = {}

        if verbose:
            print(
                "  Updating experiment config parameters in",
                task_dir / "config.yaml",
            )

        if payu_config:
            config = deep_update(config, payu_config)

        config["exe"] = str(self.model.get_exe_path(mpi=True).absolute())

        # Here we prepend inputs to the `input` list so that payu knows to use
        # our inputs over the pre-existing inputs in the config file:
        config["input"] = [
            # Note: only necessary for CABLE v2
            str(
                (
                    internal.CABLE_AUX_DIR
                    / "core"
                    / "biogeophys"
                    / "def_veg_params_zr_clitt_albedo_fix.txt"
                ).absolute()
            ),
            # Note: only necessary for CABLE v2
            str(
                (
                    internal.CABLE_AUX_DIR
                    / "core"
                    / "biogeophys"
                    / "def_soil_params.txt"
                ).absolute()
            ),
            *config.get("input", []),
        ]

        config["laboratory"] = str(internal.PAYU_LABORATORY_DIR.absolute())

        with exp_config_path.open("w", encoding="utf-8") as file:
            yaml.dump(config, file)

    def update_namelist(self, verbose=False):
        """Update the namelist file for this task."""
        nml_path = (
            internal.SPATIAL_TASKS_DIR / self.get_task_name() / internal.CABLE_NML
        )
        if verbose:
            print(f"  Adding science configurations to CABLE namelist file {nml_path}")
        patch_namelist(nml_path, self.sci_config)

        if self.model.patch:
            if verbose:
                print(
                    f"  Adding branch specific configurations to CABLE namelist file {nml_path}"
                )
            patch_namelist(nml_path, self.model.patch)

        if self.model.patch_remove:
            if verbose:
                print(
                    f"  Removing branch specific configurations from CABLE namelist file {nml_path}"
                )
            patch_remove_namelist(nml_path, self.model.patch_remove)

    def run(self, verbose=False) -> None:
        """Runs a single spatial task."""

        task_dir = internal.SPATIAL_TASKS_DIR / self.get_task_name()
        with chdir(task_dir):
            self.subprocess_handler.run_cmd(
                f"payu run {self.payu_args}" if self.payu_args else "payu run",
                verbose=verbose,
            )


def run_tasks(tasks: list[SpatialTask], verbose=False):
    """Runs tasks in `tasks` sequentially."""

    for task in tasks:
        task.run(verbose=verbose)


def get_spatial_tasks(
    models: list[Model],
    met_forcings: dict[str, str],
    science_configurations: list[dict],
    payu_args: Optional[str] = None,
):
    """Returns a list of spatial tasks to run."""
    tasks = [
        SpatialTask(
            model=model,
            met_forcing_name=met_forcing_name,
            met_forcing_payu_experiment=met_forcing_payu_experiment,
            sci_conf_id=sci_conf_id,
            sci_config=sci_config,
            payu_args=payu_args,
        )
        for model in models
        for met_forcing_name, met_forcing_payu_experiment in met_forcings.items()
        for sci_conf_id, sci_config in enumerate(science_configurations)
    ]
    return tasks
