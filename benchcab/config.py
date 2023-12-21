# Copyright 2022 ACCESS-NRI and contributors. See the top-level COPYRIGHT file for details.
# SPDX-License-Identifier: Apache-2.0

"""A module containing all *_config() functions."""
from pathlib import Path

import yaml
from cerberus import Validator

import benchcab.utils as bu


class ConfigValidationError(Exception):
    """Config validation error class."""

    def __init__(self, validator: Validator):
        """Config validation exception.

        Parameters
        ----------
        validator: cerberus.Validator
            A validation object that has been used and has the errors attribute.
        """
        # Nicely format the errors.
        errors = [f"{k} = {v}" for k, v in validator.errors.items()]

        # Assemble the error message and
        msg = "\n\nThe following errors were raised when validating the config file.\n"
        msg += "\n".join(errors) + "\n"

        # Raise to super.
        super().__init__(msg)


def validate_config(config: dict) -> bool:
    """Validate the configuration dictionary.

    Parameters
    ----------
    config : dict
        Dictionary of configuration loaded from the yaml file.

    Returns
    -------
    bool
        True if valid, exception raised otherwise.

    Raises
    ------
    ConfigValidationError
        Raised when the configuration file fails validation.
    """
    # Load the schema
    schema = bu.load_package_data("config-schema.yml")

    # Create a validator
    v = Validator(schema)

    # Validate
    is_valid = v.validate(config)

    # Valid
    if is_valid:
        return True

    # Invalid
    raise ConfigValidationError(v)


def read_config(config_path: str) -> dict:
    """Reads the config file and returns a dictionary containing the configurations.

    Parameters
    ----------
    config_path : str
        Path to the configuration file.

    Returns
    -------
    dict
        Configuration dict.

    Raises
    ------
    ConfigValidationError
        Raised when the configuration file fails validation.
    """
    # Load the configuration file.
    with Path.open(Path(config_path), "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    # Validate and return.
    validate_config(config)
    return config
