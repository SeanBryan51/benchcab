"""Singleton Logging Object."""
import logging
import sys
from typing import Union

from benchcab.utils.singleton import Singleton


class SingletonLogger(logging.Logger, metaclass=Singleton):
    def __init__(self, name: str = "benchcab", level: str = "debug"):
        """Singleton logging instance.

        Parameters
        ----------
        name : str, optional
            Name of the logger, by default 'benchcab' (this ensures singleton-ness)
        level : str, optional
            Log level, by default 'debug'
        """
        # Initialise the logger
        super(SingletonLogger, self).__init__(name=name)

        # Set level
        level = getattr(logging, level.upper())
        self.setLevel(level)

        # Create the formatter
        log_format = "%(asctime)s - %(levelname)s - %(module)s.%(filename)s:%(lineno)s - %(message)s"
        formatter = logging.Formatter(log_format)

        # Create/set the handler to point to stdout
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        self.addHandler(handler)

    def _check_multiline(self, msg: Union[str, list, tuple]) -> str:
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
            return "\n".join([str(m) for m in msg])

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
