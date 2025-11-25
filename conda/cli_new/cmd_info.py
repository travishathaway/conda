# Copyright (C) 2012 Anaconda, Inc
# SPDX-License-Identifier: BSD-3-Clause
"""
Typer command for `cx info`.

Display information about current conda installation.
"""

from argparse import ArgumentParser, Namespace
from typing import Annotated

import typer

from .helpers import JsonOption


def info(
    json: JsonOption = False,
    all: Annotated[
        bool,
        typer.Option(
            "-a",
            "--all",
            help="Show all information.",
        ),
    ] = False,
    base: Annotated[
        bool,
        typer.Option(
            "--base",
            help="Display base environment path.",
        ),
    ] = False,
    envs: Annotated[
        bool,
        typer.Option(
            "-e",
            "--envs",
            help="List all known conda environments.",
        ),
    ] = False,
    system: Annotated[
        bool,
        typer.Option(
            "-s",
            "--system",
            help="List environment variables.",
        ),
    ] = False,
    unsafe_channels: Annotated[
        bool,
        typer.Option(
            "--unsafe-channels",
            help="Display list of channels with tokens exposed.",
        ),
    ] = False,
    packages: Annotated[
        list[str] | None,
        typer.Argument(
            help="Display information about specific packages.",
        ),
    ] = None,
) -> int:
    """
    Display information about current conda install.

    Examples:

        Show all information:

            $ cx info --all

        Show base environment path:

            $ cx info --base

        List all known conda environments:

            $ cx info --envs
    """
    # Import the execute function from the original implementation
    from ..cli.main_info import execute

    # Create an argparse-compatible Namespace
    args = Namespace(
        json=json,
        all=all,
        base=base,
        envs=envs,
        system=system,
        unsafe_channels=unsafe_channels,
        packages=packages or [],
        offline=False,  # Not exposed in Typer version for simplicity
    )

    # Create a minimal parser
    parser = ArgumentParser()

    # Call the original execute function
    exit_code = execute(args, parser)

    return exit_code if isinstance(exit_code, int) else 0
