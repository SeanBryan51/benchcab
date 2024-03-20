"""Main entry point for `benchcab`."""

import shutil
import sys

from benchcab.benchcab import Benchcab
from benchcab.cli import generate_parser
from benchcab.utils import get_logger


def parse_and_dispatch(parser):
    """Parse arguments for the script and dispatch to the correct function.

    Args:
    ----
    parser : argparse.ArgumentParser
        Parser object.

    """
    args = vars(parser.parse_args(sys.argv[1:] if sys.argv[1:] else ["-h"]))

    # Intercept the verbosity flag to engage the logger
    log_level = "debug" if args.get("verbose", False) is True else "info"

    # Remove the verbose argument
    _ = args.pop("verbose")

    # We just need to instantiate this with the desired level
    get_logger(level=log_level)

    func = args.pop("func")
    func(**args)


def main():
    """Main program entry point for `benchcab`.

    This is required for setup.py entry_points
    """
    app = Benchcab(benchcab_exe_path=shutil.which(sys.argv[0]))
    parser = generate_parser(app)
    parse_and_dispatch(parser)


if __name__ == "__main__":
    main()
