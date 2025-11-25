# Copyright (C) 2012 Anaconda, Inc
# SPDX-License-Identifier: BSD-3-Clause
"""
Typer command for `cx install`.

Installs packages into a conda environment.
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


def install(
    packages: Annotated[
        list[str] | None,
        typer.Argument(
            help="Packages to install.",
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
    file: Annotated[
        list[str] | None,
        typer.Option(
            "--file",
            "-f",
            help="Read package versions from the given file.",
        ),
    ] = None,
    revision: Annotated[
        str | None,
        typer.Option(
            "--revision",
            help="Revert to the specified revision.",
        ),
    ] = None,
) -> int:
    """
    Install packages into a conda environment.

    Examples:

        Install numpy into the current environment:

            $ cx install numpy

        Install multiple packages:

            $ cx install numpy pandas scipy

        Install into a specific environment:

            $ cx install -n myenv numpy
    """
    # Import the execute function from the original implementation
    from ..cli.main_install import execute
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
        file=file or [],
        revision=revision,
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
        freeze_installed=False,
        update_deps=NULL,
        no_update_deps=NULL,
        only_deps=False,
        no_deps=False,
        prune=False,
        force=False,
        no_force=False,
    )

    # Create a minimal parser
    parser = ArgumentParser()

    # Call the original execute function
    exit_code = execute(args, parser)

    return exit_code if isinstance(exit_code, int) else 0
