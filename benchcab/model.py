# Copyright 2022 ACCESS-NRI and contributors. See the top-level COPYRIGHT file for details.
# SPDX-License-Identifier: Apache-2.0

"""Contains functions and data structures relating to CABLE models."""

import os
import shlex
import shutil
import stat
from pathlib import Path
from typing import Optional

from benchcab import internal
from benchcab.environment_modules import EnvironmentModules, EnvironmentModulesInterface
from benchcab.utils.fs import chdir, copy2, rename
from benchcab.utils.repo import GitRepo, Repo
from benchcab.utils.subprocess import SubprocessWrapper, SubprocessWrapperInterface


class Model:
    """A class used to represent a CABLE model version."""

    subprocess_handler: SubprocessWrapperInterface = SubprocessWrapper()
    modules_handler: EnvironmentModulesInterface = EnvironmentModules()

    def __init__(
        self,
        repo: Repo,
        name: Optional[str] = None,
        patch: Optional[dict] = None,
        patch_remove: Optional[dict] = None,
        build_script: Optional[str] = None,
        model_id: Optional[int] = None,
    ) -> None:
        self.repo = repo
        self.name = name if name else repo.get_branch_name()
        self.patch = patch
        self.patch_remove = patch_remove
        self.build_script = build_script
        self._model_id = model_id
        self.src_dir = Path()
        # TODO(Sean) we should not have to know whether `repo` is a `GitRepo` or
        # `SVNRepo`, we should only be working with the `Repo` interface.
        # See issue https://github.com/CABLE-LSM/benchcab/issues/210
        if isinstance(repo, GitRepo):
            self.src_dir = Path("src")

    @property
    def model_id(self) -> int:
        """Get or set the model ID."""
        if self._model_id is None:
            msg = "Attempting to access undefined model ID"
            raise RuntimeError(msg)
        return self._model_id

    @model_id.setter
    def model_id(self, value: int):
        self._model_id = value

    def get_exe_path(self, mpi=False) -> Path:
        """Return the path to the built executable."""
        return (
            internal.SRC_DIR
            / self.name
            / self.src_dir
            / "offline"
            / (internal.CABLE_MPI_EXE if mpi else internal.CABLE_EXE)
        )

    def custom_build(self, modules: list[str], verbose=False):
        """Build CABLE using a custom build script."""
        build_script_path = internal.SRC_DIR / self.name / self.build_script

        if not build_script_path.is_file():
            msg = (
                f"The build script, {build_script_path}, could not be found. "
                "Do you need to specify a different build script with the "
                "'build_script' option in config.yaml?"
            )
            raise FileNotFoundError(msg)

        tmp_script_path = build_script_path.parent / "tmp-build.sh"

        if verbose:
            print(f"Copying {build_script_path} to {tmp_script_path}")
        shutil.copy(build_script_path, tmp_script_path)

        if verbose:
            print(f"chmod +x {tmp_script_path}")
        tmp_script_path.chmod(tmp_script_path.stat().st_mode | stat.S_IEXEC)

        if verbose:
            print(
                f"Modifying {tmp_script_path.name}: remove lines that call "
                "environment modules"
            )
        remove_module_lines(tmp_script_path)

        with chdir(build_script_path.parent), self.modules_handler.load(
            modules, verbose=verbose
        ):
            self.subprocess_handler.run_cmd(
                f"./{tmp_script_path.name}",
                verbose=verbose,
            )

    def pre_build(self, mpi=False, verbose=False):
        """Runs CABLE pre-build steps."""
        path_to_repo = internal.SRC_DIR / self.name
        tmp_dir = (
            path_to_repo
            / self.src_dir
            / (internal.TMP_BUILD_DIR_MPI if mpi else internal.TMP_BUILD_DIR)
        )
        if not tmp_dir.exists():
            if verbose:
                print(f"mkdir {tmp_dir}")
            tmp_dir.mkdir()

        for pattern in internal.OFFLINE_SOURCE_FILES:
            for path in (path_to_repo / self.src_dir).glob(pattern):
                if not path.is_file():
                    continue
                copy2(path, tmp_dir, verbose=verbose)

        copy2(
            path_to_repo / self.src_dir / "offline" / "Makefile",
            tmp_dir,
            verbose=verbose,
        )

    def run_build(self, modules: list[str], mpi=False, verbose=False):
        """Runs CABLE build scripts."""
        path_to_repo = internal.SRC_DIR / self.name
        tmp_dir = (
            path_to_repo
            / self.src_dir
            / (internal.TMP_BUILD_DIR_MPI if mpi else internal.TMP_BUILD_DIR)
        )

        with chdir(tmp_dir), self.modules_handler.load(modules, verbose=verbose):
            env = os.environ.copy()
            env["NCDIR"] = f"{env['NETCDF_ROOT']}/lib/Intel"
            env["NCMOD"] = f"{env['NETCDF_ROOT']}/include/Intel"
            env["CFLAGS"] = "-O2 -fp-model precise"
            env["LDFLAGS"] = f"-L{env['NETCDF_ROOT']}/lib/Intel -O0"
            env["LD"] = "-lnetcdf -lnetcdff"
            env["FC"] = "mpif90" if mpi else "ifort"

            self.subprocess_handler.run_cmd(
                "make mpi" if mpi else "make", env=env, verbose=verbose
            )

    def post_build(self, mpi=False, verbose=False):
        """Runs CABLE post-build steps."""
        path_to_repo = internal.SRC_DIR / self.name
        tmp_dir = (
            path_to_repo
            / self.src_dir
            / (internal.TMP_BUILD_DIR_MPI if mpi else internal.TMP_BUILD_DIR)
        )
        exe = internal.CABLE_MPI_EXE if mpi else internal.CABLE_EXE

        rename(
            tmp_dir / exe,
            path_to_repo / self.src_dir / "offline" / exe,
            verbose=verbose,
        )


def remove_module_lines(file_path: Path) -> None:
    """Remove lines from `file_path` that call the environment modules package."""
    with file_path.open("r", encoding="utf-8") as file:
        contents = file.read()
    with file_path.open("w", encoding="utf-8") as file:
        for line in contents.splitlines(True):
            cmds = shlex.split(line, comments=True)
            if "module" not in cmds:
                file.write(line)
