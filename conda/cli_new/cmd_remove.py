# Copyright (C) 2012 Anaconda, Inc
# SPDX-License-Identifier: BSD-3-Clause
"""
Typer command for `cx remove`.

Removes packages from a conda environment.
"""

from argparse import ArgumentParser, Namespace
from typing import Annotated

import typer

from .helpers import (
    DryRunOption,
    OfflineOption,
    PrefixNameOption,
    PrefixPathOption,
    YesOption,
)


def remove(
    packages: Annotated[
        list[str] | None,
        typer.Argument(
            help="Packages to remove.",
        ),
    ] = None,
    name: PrefixNameOption = None,
    prefix: PrefixPathOption = None,
    yes: YesOption = False,
    dry_run: DryRunOption = False,
    offline: OfflineOption = False,
    all: Annotated[
        bool,
        typer.Option(
            "--all",
            help="Remove all packages, i.e., the entire environment.",
        ),
    ] = False,
) -> int:
    """
    Remove packages from a conda environment.

    Examples:

        Remove numpy from the current environment:

            $ cx remove numpy

        Remove multiple packages:

            $ cx remove numpy pandas scipy

        Remove from a specific environment:

            $ cx remove -n myenv numpy

        Remove all packages (delete environment):

            $ cx remove -n myenv --all
    """
    # Import the execute function from the original implementation
    from ..cli.main_remove import execute

    # Create an argparse-compatible Namespace
    args = Namespace(
        packages=packages or [],
        name=name,
        prefix=prefix,
        yes=yes,
        dry_run=dry_run,
        offline=offline,
        all=all,
        json=False,
        quiet=False,
        verbosity=0,
        # Additional args
        channel=[],
        override_channels=False,
        features=False,
        force_remove=False,
        no_pin=False,
        prune=False,
    )

    # Create a minimal parser
    parser = ArgumentParser()

    # Call the original execute function
    exit_code = execute(args, parser)

    return exit_code if isinstance(exit_code, int) else 0
