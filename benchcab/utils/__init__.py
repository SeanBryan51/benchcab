# Copyright 2022 ACCESS-NRI and contributors. See the top-level COPYRIGHT file for details.
# SPDX-License-Identifier: Apache-2.0

"""Top-level utilities."""
import pkgutil
import json
import yaml
import os
import sys
from importlib import resources
from pathlib import Path
import logging
from benchcab.utils.singleton import Singleton
from typing import Union

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


def get_logger(name='benchcab', level='debug'):
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


class SingletonLogger(logging.Logger, metaclass=Singleton):

    def __init__(self, name : str = 'benchcab', level : str = 'debug'):

        super(SingletonLogger, self).__init__(name=name)

        # Set level
        level = getattr(logging, level.upper())
        self.setLevel(level)
        
        # Create the formatter
        log_format = '%(asctime)s - %(levelname)s - %(module)s.%(filename)s:%(lineno)s - %(message)s'
        formatter = logging.Formatter(log_format)

        # Create the handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        self.addHandler(handler)
    

    def _check_multiline(self, msg : Union[str, list, tuple]) -> str:
        """Automatically join multiline output.

        Parameters
        ----------
        msg : str, list or tuple
            Message or message fragments.

        Returns
        -------
        str
            Original string or fragments joined with \n
        """

        if type(msg) in [list, tuple]:
            return '\n'.join([str(m) for m in msg])
    
        return msg

    
    def debug(self, msg, *args, **kwargs):
        """Emit a debug line, with multiline support.

        Parameters
        ----------
        msg : str or list
            Message or message fragments for additional detail.
        """
        msg = self._check_multiline(msg)
        super().debug(msg, *args, **kwargs)


    def info(self, msg, *args, **kwargs):
        """Emit a info line, with multiline support.

        Parameters
        ----------
        msg : str or list
            Message or message fragments for additional detail.
        """
        msg = self._check_multiline(msg)
        super().info(msg, *args, **kwargs)


    def warn(self, msg, *args, **kwargs):
        """Emit a warn line, with multiline support.

        Parameters
        ----------
        msg : str or list
            Message or message fragments for additional detail.
        """
        msg = self._check_multiline(msg)
        super().warn(msg, *args, **kwargs)


    def error(self, msg, *args, **kwargs):
        """Emit a error line, with multiline support.

        Parameters
        ----------
        msg : str or list
            Message or message fragments for additional detail.
        """
        msg = self._check_multiline(msg)
        super().error(msg, *args, **kwargs)


    def critical(self, msg, *args, **kwargs):
        """Emit a critical line, with multiline support.

        Parameters
        ----------
        msg : str or list
            Message or message fragments for additional detail.
        """
        msg = self._check_multiline(msg)
        super().critical(msg, *args, **kwargs)