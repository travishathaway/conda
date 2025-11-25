# Copyright (C) 2012 Anaconda, Inc
# SPDX-License-Identifier: BSD-3-Clause
"""
Typer commands for `cx env` subcommands.

Manage conda environments.
"""

from argparse import ArgumentParser, Namespace
from typing import Annotated

import typer

from .helpers import JsonOption, PrefixNameOption, PrefixPathOption, YesOption

# Create a nested Typer app for env subcommands
env_app = typer.Typer(
    name="env",
    help="Manage conda environments",
    no_args_is_help=True,
)


@env_app.command(name="list")
def env_list(
    json: JsonOption = False,
) -> int:
    """
    List all known conda environments.

    Examples:

        List all environments:

            $ cx env list

        List in JSON format:

            $ cx env list --json
    """
    # Import the execute function from the original implementation
    from ..cli.main_env_list import execute

    # Create an argparse-compatible Namespace
    args = Namespace(
        json=json,
        quiet=False,
        verbosity=0,
    )

    # Create a minimal parser
    parser = ArgumentParser()

    # Call the original execute function
    exit_code = execute(args, parser)

    return exit_code if isinstance(exit_code, int) else 0


@env_app.command(name="create")
def env_create(
    name: PrefixNameOption = None,
    prefix: PrefixPathOption = None,
    file: Annotated[
        list[str] | None,
        typer.Option(
            "-f",
            "--file",
            help="Environment definition file (environment.yml).",
        ),
    ] = None,
    yes: YesOption = False,
) -> int:
    """
    Create an environment from an environment.yml file.

    Examples:

        Create environment from file:

            $ cx env create -f environment.yml

        Create with specific name:

            $ cx env create -n myenv -f environment.yml
    """
    # Import the execute function from the original implementation
    from ..cli.main_env_create import execute
    from ..common.constants import NULL

    # Create an argparse-compatible Namespace
    args = Namespace(
        name=name,
        prefix=prefix,
        file=file[0] if file else None,
        yes=yes,
        json=False,
        quiet=False,
        verbosity=0,
        # Additional args
        force=False,
        remote_definition=None,
        solver=NULL,
        channel=[],
        override_channels=False,
        dry_run=False,
    )

    # Create a minimal parser
    parser = ArgumentParser()

    # Call the original execute function
    exit_code = execute(args, parser)

    return exit_code if isinstance(exit_code, int) else 0


@env_app.command(name="remove")
def env_remove(
    name: PrefixNameOption = None,
    prefix: PrefixPathOption = None,
    yes: YesOption = False,
) -> int:
    """
    Remove an environment.

    Examples:

        Remove environment by name:

            $ cx env remove -n myenv

        Remove environment by path:

            $ cx env remove -p /path/to/env
    """
    # Import the execute function from the original implementation
    from ..cli.main_env_remove import execute

    if not name and not prefix:
        typer.echo("Error: Either --name or --prefix is required", err=True)
        raise typer.Exit(1)

    # Create an argparse-compatible Namespace
    args = Namespace(
        name=name,
        prefix=prefix,
        yes=yes,
        json=False,
        quiet=False,
        verbosity=0,
        # Additional args
        all=True,  # env remove always removes all packages
        dry_run=False,
    )

    # Create a minimal parser
    parser = ArgumentParser()

    # Call the original execute function
    exit_code = execute(args, parser)

    return exit_code if isinstance(exit_code, int) else 0


@env_app.command(name="update")
def env_update(
    name: PrefixNameOption = None,
    prefix: PrefixPathOption = None,
    file: Annotated[
        str | None,
        typer.Option(
            "-f",
            "--file",
            help="Environment definition file (environment.yml).",
        ),
    ] = None,
    prune: Annotated[
        bool,
        typer.Option(
            "--prune",
            help="Remove installed packages not defined in environment.yml.",
        ),
    ] = False,
) -> int:
    """
    Update an environment from an environment.yml file.

    Examples:

        Update environment from file:

            $ cx env update -f environment.yml

        Update and prune extra packages:

            $ cx env update -f environment.yml --prune
    """
    # Import the execute function from the original implementation
    from ..cli.main_env_update import execute
    from ..common.constants import NULL

    # Create an argparse-compatible Namespace
    args = Namespace(
        name=name,
        prefix=prefix,
        file=file,
        prune=prune,
        json=False,
        quiet=False,
        verbosity=0,
        # Additional args
        solver=NULL,
        channel=[],
        override_channels=False,
        dry_run=False,
        yes=False,
    )

    # Create a minimal parser
    parser = ArgumentParser()

    # Call the original execute function
    exit_code = execute(args, parser)

    return exit_code if isinstance(exit_code, int) else 0


@env_app.command(name="config")
def env_config(
    name: PrefixNameOption = None,
    prefix: PrefixPathOption = None,
    json: JsonOption = False,
) -> int:
    """
    Configure environment-specific settings.

    Examples:

        View config for environment:

            $ cx env config -n myenv
    """
    # Import the execute function from the original implementation
    from ..cli.main_env_config import execute

    # Create an argparse-compatible Namespace
    args = Namespace(
        name=name,
        prefix=prefix,
        json=json,
        quiet=False,
        verbosity=0,
        # Additional args - env config has many subcommands
        # For simplicity, just pass minimal args
        vars=Namespace(subcommand="vars", list=True),
    )

    # Create a minimal parser
    parser = ArgumentParser()

    # Call the original execute function
    exit_code = execute(args, parser)

    return exit_code if isinstance(exit_code, int) else 0
