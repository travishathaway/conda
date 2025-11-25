# Copyright (C) 2012 Anaconda, Inc
# SPDX-License-Identifier: BSD-3-Clause
"""
Typer command for `cx list`.

Lists all packages installed into an environment.
"""

from argparse import ArgumentParser, Namespace
from typing import Annotated

import typer

from .helpers import JsonOption, PrefixNameOption, PrefixPathOption


def list_packages(
    regex: Annotated[
        str | None,
        typer.Argument(
            help="List only packages matching this regular expression.",
        ),
    ] = None,
    name: PrefixNameOption = None,
    prefix: PrefixPathOption = None,
    json: JsonOption = False,
    show_channel_urls: Annotated[
        bool | None,
        typer.Option(
            "--show-channel-urls/--no-show-channel-urls",
            help="Show channel urls. Overrides conda config show_channel_urls.",
        ),
    ] = None,
    fields: Annotated[
        str | None,
        typer.Option(
            "--fields",
            help="Comma-separated list of fields to print.",
        ),
    ] = None,
    reverse: Annotated[
        bool,
        typer.Option(
            "--reverse",
            help="List installed packages in reverse order.",
        ),
    ] = False,
    canonical: Annotated[
        bool,
        typer.Option(
            "-c",
            "--canonical",
            help="Output canonical names of packages only.",
        ),
    ] = False,
    full_name: Annotated[
        bool,
        typer.Option(
            "-f",
            "--full-name",
            help="Only search for full names, i.e., ^<regex>$.",
        ),
    ] = False,
    explicit: Annotated[
        bool,
        typer.Option(
            "--explicit",
            help="List explicitly all installed conda packages with URL.",
        ),
    ] = False,
    md5: Annotated[
        bool,
        typer.Option(
            "--md5",
            help="Add MD5 hashsum when using --explicit.",
        ),
    ] = False,
    sha256: Annotated[
        bool,
        typer.Option(
            "--sha256",
            help="Add SHA256 hashsum when using --explicit.",
        ),
    ] = False,
    export: Annotated[
        bool,
        typer.Option(
            "-e",
            "--export",
            help="Output explicit, machine-readable requirement strings.",
        ),
    ] = False,
    revisions: Annotated[
        bool,
        typer.Option(
            "-r",
            "--revisions",
            help="List the revision history.",
        ),
    ] = False,
    no_pip: Annotated[
        bool,
        typer.Option(
            "--no-pip",
            help="Do not include pip-only installed packages.",
        ),
    ] = False,
    auth: Annotated[
        bool,
        typer.Option(
            "--auth",
            help="In explicit mode, keep authentication details in package URLs.",
        ),
    ] = False,
) -> int:
    """
    List installed packages in a conda environment.

    Examples:

        List all packages in the current environment:

            $ cx list

        List all packages in reverse order:

            $ cx list --reverse

        List all packages installed into the environment 'myenv':

            $ cx list -n myenv

        List all packages that begin with the letters "py", using regex:

            $ cx list ^py

        Save packages for future use:

            $ cx list --export > package-list.txt
    """
    # Import the execute function from the original implementation
    from ..cli.main_list import execute

    # Create an argparse-compatible Namespace
    args = Namespace(
        regex=regex,
        name=name,
        prefix=prefix,
        json=json,
        show_channel_urls=show_channel_urls,
        list_fields=fields.split(",") if fields else None,
        reverse=reverse,
        canonical=canonical,
        full_name=full_name,
        explicit=explicit,
        md5=md5,
        sha256=sha256,
        export=export,
        revisions=revisions,
        pip=not no_pip,
        remove_auth=not auth,
    )

    # Create a minimal parser (not used in execute, but required by signature)
    parser = ArgumentParser()

    # Call the original execute function
    exit_code = execute(args, parser)

    return exit_code if isinstance(exit_code, int) else 0
