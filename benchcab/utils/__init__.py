# Copyright 2022 ACCESS-NRI and contributors. See the top-level COPYRIGHT file for details.
# SPDX-License-Identifier: Apache-2.0

"""Top-level utilities."""
import pkgutil
import json
import yaml
import os
from importlib import resources
from pathlib import Path
from jinja2 import Environment, BaseLoader


# List of one-argument decoding functions.
PACKAGE_DATA_DECODERS = dict(
    json=json.loads,
    yml=yaml.safe_load
)


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

    # If there is no explicit decoder, just return the raw text
    if ext not in PACKAGE_DATA_DECODERS.keys():
        return raw

    # Decode and return.
    return PACKAGE_DATA_DECODERS[ext](raw)


def interpolate_string_template(template, **kwargs):
    """Interpolate a string template with kwargs.

    Parameters
    ----------
    template : str
        Template string to interpolate over.

    Returns
    -------
    str
        Interpolated string.
    """
    _template = Environment(loader=BaseLoader()).from_string(template)
    return _template.render(**kwargs)


def interpolate_file_template(template_file, **kwargs):
    """Interpolate kwargs directly into a j2 template file from the data directory.

    Parameters
    ----------
    template_file : str
        Filepath slug in the benchcab data directory.

    Returns
    -------
    str
        Interpolated template string.
    """
    template = load_package_data(template_file)
    return interpolate_string_template(template, **kwargs)