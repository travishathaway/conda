# Copyright (C) 2012 Anaconda, Inc
# SPDX-License-Identifier: BSD-3-Clause
"""
Reusable Typer options and utilities for the cx CLI.

This module provides shared options and validators to maintain consistency
across commands while leveraging Typer's type-based approach.
"""

from typing import Annotated

import typer

from ..base.context import context


def validate_prefix_name(name: str | None, prefix: str | None) -> None:
    """
    Validate that either name or prefix is provided, but not both.

    Raises:
        typer.BadParameter: If both or neither are provided when one is required.
    """
    if name and prefix:
        raise typer.BadParameter("Cannot specify both --name and --prefix")


# Common option type aliases using Annotated for reusability
PrefixNameOption = Annotated[
    str | None,
    typer.Option(
        "-n",
        "--name",
        help="Name of environment",
        metavar="ENVIRONMENT",
    ),
]

PrefixPathOption = Annotated[
    str | None,
    typer.Option(
        "-p",
        "--prefix",
        help="Full path to environment location (i.e. prefix)",
        metavar="PATH",
    ),
]

JsonOption = Annotated[
    bool,
    typer.Option(
        "--json",
        help="Report all output as json. Suitable for using conda programmatically.",
    ),
]

VerboseOption = Annotated[
    bool,
    typer.Option(
        "-v",
        "--verbose",
        help="Use once for info, twice for debug, three times for trace.",
        count=True,
    ),
]

QuietOption = Annotated[
    bool,
    typer.Option(
        "-q",
        "--quiet",
        help="Do not display progress bar.",
    ),
]

DryRunOption = Annotated[
    bool,
    typer.Option(
        "--dry-run",
        help="Only display what would have been done.",
    ),
]

DownloadOnlyOption = Annotated[
    bool,
    typer.Option(
        "--download-only",
        help="Solve an environment and ensure package caches are populated, but exit "
        "prior to unlinking and linking packages into the prefix.",
    ),
]

YesOption = Annotated[
    bool,
    typer.Option(
        "-y",
        "--yes",
        help="Do not ask for confirmation.",
    ),
]

ChannelOption = Annotated[
    list[str] | None,
    typer.Option(
        "-c",
        "--channel",
        help="Additional channel to search for packages. These are URLs searched in the "
        "order they are given (including file:// for local directories). Then, the "
        "defaults or channels from .condarc are searched (unless --override-channels "
        "is given). You can use 'defaults' to get the default packages for conda. You "
        "can also use any name and the .condarc channel_alias value will be prepended. "
        "The default channel_alias is https://conda.anaconda.org/.",
        metavar="CHANNEL",
    ),
]

OverrideChannelsOption = Annotated[
    bool,
    typer.Option(
        "--override-channels",
        help="Do not search default or .condarc channels. Requires --channel.",
    ),
]

ShowChannelUrlsOption = Annotated[
    bool,
    typer.Option(
        "--show-channel-urls/--no-show-channel-urls",
        help="Show channel urls. Overrides the value given by conda config --show show_channel_urls.",
    ),
]

UseLocalOption = Annotated[
    bool,
    typer.Option(
        "--use-local",
        help="Use locally built packages. Identical to '-c local'.",
    ),
]

OfflineOption = Annotated[
    bool,
    typer.Option(
        "--offline",
        help="Offline mode. Don't connect to the Internet.",
    ),
]

SolverOption = Annotated[
    str | None,
    typer.Option(
        "--solver",
        help="Choose which solver backend to use.",
        metavar="SOLVER",
    ),
]

NoPinOption = Annotated[
    bool,
    typer.Option(
        "--no-pin",
        help="Ignore pinned file.",
    ),
]

NoDefaultPackagesOption = Annotated[
    bool,
    typer.Option(
        "--no-default-packages",
        help="Ignore create_default_packages in the .condarc file.",
    ),
]

CopyOption = Annotated[
    bool,
    typer.Option(
        "--copy",
        help="Install all packages using copies instead of hard- or soft-linking.",
    ),
]


def get_prefix(name: str | None, prefix: str | None) -> str:
    """
    Get the target prefix from name or prefix option.

    Args:
        name: Environment name
        prefix: Environment path

    Returns:
        The resolved prefix path

    Raises:
        typer.BadParameter: If validation fails
    """
    from ..base.context import locate_prefix_by_name

    if name and prefix:
        raise typer.BadParameter("Cannot specify both --name and --prefix")

    if name:
        return locate_prefix_by_name(name)
    elif prefix:
        return prefix
    else:
        return context.target_prefix


def validate_package_specs(packages: list[str]) -> None:
    """
    Validate package specifications.

    Args:
        packages: List of package specs to validate

    Raises:
        typer.BadParameter: If validation fails
    """
    from ..base.context import validate_channels
    from ..models.match_spec import MatchSpec

    try:
        validate_channels(
            channel
            for spec in map(MatchSpec, packages)
            if (channel := spec.get_exact_value("channel"))
        )
    except Exception as e:
        raise typer.BadParameter(str(e)) from e
