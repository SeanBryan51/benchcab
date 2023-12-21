# Copyright 2022 ACCESS-NRI and contributors. See the top-level COPYRIGHT file for details.
# SPDX-License-Identifier: Apache-2.0

"""Top-level utilities."""
import json
import os
import pkgutil
from importlib import resources
from pathlib import Path

import yaml

from benchcab.utils.singleton_logger import SingletonLogger

# List of one-argument decoding functions.
PACKAGE_DATA_DECODERS = dict(json=json.loads, yml=yaml.safe_load)


def get_installed_root() -> Path:
    """Get the installed root of the benchcab installation.

    Returns
    -------
    Path
        Path to the installed root.
    """
    return Path(resources.files("benchcab"))


def load_package_data(filename: str) -> dict:
    """Load data out of the installed package data directory.

    Parameters
    ----------
    filename : str
        Filename of the file to load out of the data directory.
    """
    # Work out the encoding of requested file.
    ext = filename.split(".")[-1]

    # Alias yaml and yml.
    ext = ext if ext != "yaml" else "yml"

    # Extract from the installations data directory.
    raw = pkgutil.get_data("benchcab", os.path.join("data", filename)).decode("utf-8")

    # Decode and return.
    return PACKAGE_DATA_DECODERS[ext](raw)


def get_logger(name="benchcab", level="debug"):
    """Get a singleton logger object.

    Parameters
    ----------
    name : str, optional
        Name of the logger, by default 'benchcab'
    level : str, optional
        Level of logging, by default 'debug'

    Returns
    -------
    benchcab.utils.SingletonLogger
        Logger instance.
    """
    return SingletonLogger(name=name, level=level)
