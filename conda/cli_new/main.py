# Copyright (C) 2012 Anaconda, Inc
# SPDX-License-Identifier: BSD-3-Clause
"""
Main Typer-based CLI entry point for cx.

This module implements an alternative CLI using Typer that reuses
the business logic from the argparse-based conda CLI.
"""

import sys
from typing import Annotated

import typer

from ..base.context import context
from ..common.compat import ensure_text_type
from ..exception_handler import conda_exception_handler

# Create the main Typer app
app = typer.Typer(
    name="cx",
    help="Conda package manager (Typer-based CLI)",
    no_args_is_help=True,
    pretty_exceptions_enable=False,  # We use our own exception handler
)


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        from .. import __version__

        typer.echo(f"cx {__version__}")
        raise typer.Exit()


def init_loggers() -> None:
    """Initialize conda loggers."""
    import logging

    from ..gateways.logging import initialize_logging, set_log_level

    initialize_logging()

    # silence logging info to avoid interfering with JSON output
    if context.json:
        for logger in ("conda.stdout.verbose", "conda.stdoutlog", "conda.stderrlog"):
            logging.getLogger(logger).setLevel(logging.CRITICAL + 10)

    # set log_level
    set_log_level(context.log_level)


def pre_command_callback(
    ctx: typer.Context,
    json: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Report all output as json. Suitable for using conda programmatically.",
        ),
    ] = False,
    debug: Annotated[
        bool,
        typer.Option(
            "--debug",
            help="Show debug output.",
        ),
    ] = False,
    trace: Annotated[
        bool,
        typer.Option(
            "--trace",
            help="Show trace output (very verbose).",
        ),
    ] = False,
    verbose: Annotated[
        int,
        typer.Option(
            "-v",
            "--verbose",
            count=True,
            help="Use once for info, twice for debug, three times for trace.",
        ),
    ] = 0,
    version: Annotated[
        bool | None,
        typer.Option(
            "-V",
            "--version",
            callback=version_callback,
            is_eager=True,
            help="Show the conda version number and exit.",
        ),
    ] = None,
    no_plugins: Annotated[
        bool,
        typer.Option(
            "--no-plugins",
            help="Disable all plugins that are not built into conda.",
        ),
    ] = False,
) -> None:
    """
    Global callback for pre-command initialization.

    This handles context initialization before any command executes,
    similar to the pre-parsing in the argparse version.
    """

    # Create a simple namespace object to pass to context init
    class SimpleNamespace:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    # Calculate verbosity
    verbosity = verbose
    if debug:
        verbosity = 2
    if trace:
        verbosity = 3

    # Create argparse-compatible namespace
    pre_args = SimpleNamespace(
        json=json,
        debug=debug,
        trace=trace,
        verbosity=verbosity,
        no_plugins=no_plugins,
    )

    # Initialize context (first pass)
    context.__init__(argparse_args=pre_args)

    if context.no_plugins:
        context.plugin_manager.disable_external_plugins()

    # Reinitialize in case any of the entrypoints modified the context
    context.__init__(argparse_args=pre_args)

    # Store for commands to access
    ctx.obj = {"context_initialized": True}


# Set the callback on the app
app.callback(invoke_without_command=False)(pre_command_callback)


def main_impl() -> int:
    """
    Implementation of main entry point.

    Returns:
        Exit code
    """
    # Import and register all commands
    from . import (
        cmd_create,
        cmd_env,
        cmd_info,
        cmd_install,
        cmd_list,
        cmd_remove,
        cmd_search,
        cmd_update,
    )
    from .plugins import register_plugin_commands

    # Register built-in commands
    app.command(name="list")(cmd_list.list_packages)
    app.command(name="info")(cmd_info.info)
    app.command(name="create")(cmd_create.create)
    app.command(name="install")(cmd_install.install)
    app.command(name="remove")(cmd_remove.remove)
    app.command(name="update")(cmd_update.update)
    app.command(name="search")(cmd_search.search)

    # Register nested env commands
    app.add_typer(cmd_env.env_app, name="env")

    # Register plugin commands
    register_plugin_commands(app)

    # Initialize loggers after context is set up
    init_loggers()

    # Run the app
    return app()


def main() -> int:
    """
    Main entry point for cx CLI.

    This wraps the Typer app with conda's exception handler
    to maintain consistent error handling behavior.
    """
    # Cleanup argv
    args = sys.argv[1:]  # drop executable/script
    args = tuple(ensure_text_type(s) for s in args)

    # Check for shell activation (conda activate/deactivate)
    if args and args[0].strip().startswith("shell."):
        # Delegate to the original shell handler
        from ..cli.main import main_sourced

        return conda_exception_handler(main_sourced, *args)

    # Wrap in exception handler
    def _run():
        try:
            # Set sys.argv for Typer to parse
            sys.argv = ["cx"] + list(args)
            return main_impl()
        except SystemExit as e:
            # Typer raises SystemExit with the code
            return e.code if isinstance(e.code, int) else (1 if e.code else 0)

    result = conda_exception_handler(_run)
    return result if isinstance(result, int) else 0


if __name__ == "__main__":
    sys.exit(main())
