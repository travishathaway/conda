# Copyright (C) 2012 Anaconda, Inc
# SPDX-License-Identifier: BSD-3-Clause
"""
Typer command for `cx search`.

Search for packages in conda channels.
"""

from argparse import ArgumentParser, Namespace
from typing import Annotated

import typer

from .helpers import (
    ChannelOption,
    JsonOption,
    OfflineOption,
    OverrideChannelsOption,
)


def search(
    query: Annotated[
        str | None,
        typer.Argument(
            help="Search query (package name or pattern).",
        ),
    ] = None,
    json: JsonOption = False,
    channel: ChannelOption = None,
    override_channels: OverrideChannelsOption = False,
    offline: OfflineOption = False,
    info: Annotated[
        bool,
        typer.Option(
            "--info",
            "-i",
            help="Provide detailed information about each package.",
        ),
    ] = False,
) -> int:
    """
    Search for packages in conda channels.

    Examples:

        Search for numpy:

            $ cx search numpy

        Search with wildcards:

            $ cx search "num*"

        Search in specific channel:

            $ cx search -c conda-forge numpy
    """
    # Import the execute function from the original implementation
    from ..cli.main_search import execute
    from ..common.constants import NULL

    # Create an argparse-compatible Namespace
    args = Namespace(
        match_spec=query,
        json=json,
        channel=channel or [],
        override_channels=override_channels,
        offline=offline,
        info=info,
        quiet=False,
        verbosity=0,
        # Additional args
        use_local=False,
        spec=False,
        reverse_dependency=False,
        outdated=False,
        canonical=False,
        names_only=False,
        platform=NULL,
        subdir=NULL,
    )

    # Create a minimal parser
    parser = ArgumentParser()

    # Call the original execute function
    exit_code = execute(args, parser)

    return exit_code if isinstance(exit_code, int) else 0
