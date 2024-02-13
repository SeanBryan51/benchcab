# Copyright 2022 ACCESS-NRI and contributors. See the top-level COPYRIGHT file for details.
# SPDX-License-Identifier: Apache-2.0

# ruff: noqa: PTH118

"""Top-level utilities."""
import json
import logging
import os
import pkgutil
import sys
from importlib import resources
from pathlib import Path

import yaml

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
    """Get a logger instance.

    Parameters
    ----------
    name : str, optional
        Name, by default 'benchcab'
    level : str, optional
        Level, by default 'debug'

    Returns
    -------
    logging.Logger
        A logger instance guaranteed to be singleton if called with the same params.

    """
    # Get or create a logger
    logger = logging.getLogger(name)

    # Workaround for native singleton property.
    # NOTE: This will ignore the provided level and give you whatever was first set.
    if logger.level != logging.NOTSET:
        return logger

    # Set the level
    level = getattr(logging, level.upper())
    logger.setLevel(level)

    # Create the formatter
    log_format = (
        "%(asctime)s - %(levelname)s - %(module)s.%(filename)s:%(lineno)s - %(message)s"
    )
    formatter = logging.Formatter(log_format)

    # Create/set the handler to point to stdout
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
