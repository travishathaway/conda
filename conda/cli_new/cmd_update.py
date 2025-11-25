# Copyright (C) 2012 Anaconda, Inc
# SPDX-License-Identifier: BSD-3-Clause
"""
Typer command for `cx update`.

Updates packages in a conda environment.
"""

from argparse import ArgumentParser, Namespace
from typing import Annotated

import typer

from .helpers import (
    ChannelOption,
    DryRunOption,
    OfflineOption,
    OverrideChannelsOption,
    PrefixNameOption,
    PrefixPathOption,
    SolverOption,
    YesOption,
)


def update(
    packages: Annotated[
        list[str] | None,
        typer.Argument(
            help="Packages to update.",
        ),
    ] = None,
    name: PrefixNameOption = None,
    prefix: PrefixPathOption = None,
    channel: ChannelOption = None,
    override_channels: OverrideChannelsOption = False,
    solver: SolverOption = None,
    yes: YesOption = False,
    dry_run: DryRunOption = False,
    offline: OfflineOption = False,
    all: Annotated[
        bool,
        typer.Option(
            "--all",
            help="Update all installed packages in the environment.",
        ),
    ] = False,
) -> int:
    """
    Update packages in a conda environment.

    Examples:

        Update numpy in the current environment:

            $ cx update numpy

        Update multiple packages:

            $ cx update numpy pandas scipy

        Update all packages:

            $ cx update --all

        Update in a specific environment:

            $ cx update -n myenv numpy
    """
    # Import the execute function from the original implementation
    from ..cli.main_update import execute
    from ..common.constants import NULL

    # Create an argparse-compatible Namespace
    args = Namespace(
        packages=packages or [],
        name=name,
        prefix=prefix,
        channel=channel or [],
        override_channels=override_channels,
        solver=solver,
        yes=yes,
        dry_run=dry_run,
        offline=offline,
        all=all,
        json=False,
        quiet=False,
        verbosity=0,
        # Additional args
        download_only=False,
        show_channel_urls=NULL,
        use_local=False,
        no_pin=False,
        copy=False,
        force_reinstall=False,
        update_deps=NULL,
        no_update_deps=NULL,
        only_deps=False,
        no_deps=False,
        prune=False,
        force=False,
        file=[],
    )

    # Create a minimal parser
    parser = ArgumentParser()

    # Call the original execute function
    exit_code = execute(args, parser)

    return exit_code if isinstance(exit_code, int) else 0
