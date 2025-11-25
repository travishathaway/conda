# Copyright (C) 2012 Anaconda, Inc
# SPDX-License-Identifier: BSD-3-Clause
"""
Plugin integration for the Typer-based CLI.

This module handles dynamic registration of plugin-provided subcommands.
"""

import logging

import typer

log = logging.getLogger(__name__)

# Built-in commands that plugins cannot override
BUILTIN_COMMANDS = {
    "list",
    "info",
    "create",
    "install",
    "remove",
    "update",
    "search",
    "env",
}


def register_plugin_commands(app: typer.Typer) -> None:
    """
    Register plugin-provided subcommands with the Typer app.

    Args:
        app: The main Typer application instance

    This function discovers and registers plugin subcommands,
    maintaining compatibility with conda's plugin system.
    """
    from ..base.context import context

    if not hasattr(context, "plugin_manager"):
        log.debug("Plugin manager not available")
        return

    try:
        plugin_subcommands = context.plugin_manager.get_subcommands()
    except Exception as e:
        log.warning(f"Failed to get plugin subcommands: {e}")
        return

    for name, plugin_command in plugin_subcommands.items():
        if name in BUILTIN_COMMANDS:
            log.warning(
                f"Plugin subcommand '{name}' conflicts with built-in command, skipping"
            )
            continue

        # Create a wrapper to adapt plugin to Typer
        def create_plugin_wrapper(plugin_cmd, cmd_name):
            """Create a wrapper function for the plugin command."""
            import typer

            def plugin_wrapper(ctx: typer.Context) -> int:
                """Wrapper to execute plugin command."""
                # Plugins may have their own argument parsing
                # For now, pass remaining args to the plugin
                from argparse import Namespace

                # Create a minimal namespace for compatibility
                args = Namespace()
                args.cmd = cmd_name

                # Try to execute the plugin
                try:
                    if hasattr(plugin_cmd, "configure_parser"):
                        # Standard plugin with configure_parser
                        # We'd need to create an argparse subparser here
                        # For now, log that this plugin style needs adaptation
                        log.warning(
                            f"Plugin '{cmd_name}' uses configure_parser, "
                            "which requires adaptation for Typer"
                        )
                        typer.echo(
                            f"Plugin command '{cmd_name}' is not yet fully supported in cx",
                            err=True,
                        )
                        return 1
                    elif callable(plugin_cmd):
                        # Direct callable plugin
                        return plugin_cmd(args, None) or 0
                    else:
                        log.error(f"Plugin '{cmd_name}' has unsupported format")
                        return 1
                except Exception as e:
                    log.error(f"Error executing plugin '{cmd_name}': {e}")
                    typer.echo(f"Error: {e}", err=True)
                    return 1

            plugin_wrapper.__name__ = f"plugin_{cmd_name}"
            plugin_wrapper.__doc__ = f"Plugin command: {cmd_name}"
            return plugin_wrapper

        # Register the plugin command
        try:
            wrapper = create_plugin_wrapper(plugin_command, name)
            app.command(name=name, help=f"Plugin command: {name}")(wrapper)
            log.debug(f"Registered plugin command: {name}")
        except Exception as e:
            log.warning(f"Failed to register plugin command '{name}': {e}")
