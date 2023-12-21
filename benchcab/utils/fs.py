# Copyright 2022 ACCESS-NRI and contributors. See the top-level COPYRIGHT file for details.
# SPDX-License-Identifier: Apache-2.0

"""Contains utility functions for interacting with the file system."""

import contextlib
import os
import shutil
from pathlib import Path


@contextlib.contextmanager
def chdir(newdir: Path):
    """Context manager `cd`."""
    prevdir = Path.cwd()
    os.chdir(newdir.expanduser())
    try:
        yield
    finally:
        os.chdir(prevdir)


def rename(src: Path, dest: Path, verbose=False):
    """A wrapper around `pathlib.Path.rename` with optional loggging."""
    if verbose:
        print(f"mv {src} {dest}")
    src.rename(dest)


def copy2(src: Path, dest: Path, verbose=False):
    """A wrapper around `shutil.copy2` with optional logging."""
    if verbose:
        print(f"cp -p {src} {dest}")
    shutil.copy2(src, dest)


def next_path(path_pattern: str, path: Path = Path(), sep: str = "-") -> Path:
    """Find the next free path.

    Finds the next free path in a sequentially named list of
    files with the following pattern in the `path` directory:

    path_pattern = 'file{sep}*.suf':

    file-1.txt
    file-2.txt
    file-3.txt
    """
    loc_pattern = Path(path_pattern)
    new_file_index = 1
    common_filename, _ = loc_pattern.stem.split(sep)

    pattern_files_sorted = sorted(path.glob(path_pattern))
    if pattern_files_sorted != []:
        common_filename, last_file_index = pattern_files_sorted[-1].stem.split(sep)
        new_file_index = int(last_file_index) + 1

    return Path(f"{common_filename}{sep}{new_file_index}{loc_pattern.suffix}")


def mkdir(new_path: Path, verbose=False, **kwargs):
    """Create the `new_path` directory.

    Parameters
    ----------
    new_path : Path
        Path to the directory to be created.
    verbose : bool, default False
        Additional level of logging if True
    **kwargs : dict, optional
        Additional options for `pathlib.Path.mkdir()`
    """
    if verbose:
        print(f"Creating {new_path} directory")
    new_path.mkdir(**kwargs)
