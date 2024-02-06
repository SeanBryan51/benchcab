"""Singleton Object."""


class Singleton(type):
    """Singleton base (meta) class."""

    _instances = {}

    def __call__(cls, *args, **kwargs):
        """Create the object on first call, return otherwise.

        Returns
        -------
        object
            The object that metaclasses this base class.

        """
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)

        return cls._instances[cls]
