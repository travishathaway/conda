# Copyright (C) 2012 Anaconda, Inc
# SPDX-License-Identifier: BSD-3-Clause
"""
Typer command for `cx create`.

Creates new conda environments with the specified packages.
"""

from argparse import Namespace
from typing import Annotated

import typer

from ..base.context import context
from .helpers import (
    ChannelOption,
    CopyOption,
    DownloadOnlyOption,
    DryRunOption,
    JsonOption,
    NoPinOption,
    OfflineOption,
    OverrideChannelsOption,
    PrefixNameOption,
    PrefixPathOption,
    QuietOption,
    ShowChannelUrlsOption,
    SolverOption,
    UseLocalOption,
    YesOption,
)


def create(
    packages: Annotated[
        list[str] | None,
        typer.Argument(
            help="List of packages to install or update in the conda environment.",
            metavar="package_spec",
        ),
    ] = None,
    # Target Environment Specification
    name: PrefixNameOption = None,
    prefix: PrefixPathOption = None,
    # Basic options
    clone: Annotated[
        str | None,
        typer.Option(
            "--clone",
            help="Create a new environment as a copy of an existing local environment.",
            metavar="ENV",
        ),
    ] = None,
    file: Annotated[
        list[str] | None,
        typer.Option(
            "--file",
            help="Read package versions from the given file. Repeated file specifications can be passed.",
        ),
    ] = None,
    dev: Annotated[
        bool,
        typer.Option(
            "--dev",
            help="Use `sys.executable -m conda` in wrapper scripts instead of CONDA_EXE.",
        ),
    ] = False,
    # Channel Customization
    channel: ChannelOption = None,
    use_local: UseLocalOption = False,
    override_channels: OverrideChannelsOption = False,
    repodata_fn: Annotated[
        list[str] | None,
        typer.Option(
            "--repodata-fn",
            help="Specify file name of repodata on the remote server.",
        ),
    ] = None,
    experimental: Annotated[
        str | None,
        typer.Option(
            "--experimental",
            help="Enable experimental features (jlap, lock).",
        ),
    ] = None,
    no_lock: Annotated[
        bool,
        typer.Option(
            "--no-lock",
            help="Disable locking when reading, updating index cache.",
        ),
    ] = False,
    repodata_use_zst: Annotated[
        bool | None,
        typer.Option(
            "--repodata-use-zst/--no-repodata-use-zst",
            help="Check for/do not check for repodata.json.zst.",
        ),
    ] = None,
    subdir: Annotated[
        str | None,
        typer.Option(
            "--subdir",
            "--platform",
            help="Use packages built for this platform (e.g., 'osx-64', 'linux-64').",
            metavar="SUBDIR",
        ),
    ] = None,
    # Solver Mode Modifiers
    strict_channel_priority: Annotated[
        bool,
        typer.Option(
            "--strict-channel-priority",
            help="Packages in lower priority channels are not considered if package exists in higher priority channel.",
        ),
    ] = False,
    no_channel_priority: Annotated[
        bool,
        typer.Option(
            "--no-channel-priority",
            help="Package version takes precedence over channel priority.",
        ),
    ] = False,
    no_deps: Annotated[
        bool,
        typer.Option(
            "--no-deps",
            help="Do not install, update, remove, or change dependencies.",
        ),
    ] = False,
    only_deps: Annotated[
        bool,
        typer.Option(
            "--only-deps",
            help="Only install dependencies.",
        ),
    ] = False,
    no_pin: NoPinOption = False,
    no_default_packages: Annotated[
        bool,
        typer.Option(
            "--no-default-packages",
            help="Ignore create_default_packages in the .condarc file.",
        ),
    ] = False,
    solver: SolverOption = None,
    # Package Linking and Install-time Options
    copy: CopyOption = False,
    no_shortcuts: Annotated[
        bool,
        typer.Option(
            "--no-shortcuts",
            help="Don't install start menu shortcuts.",
        ),
    ] = False,
    shortcuts_only: Annotated[
        list[str] | None,
        typer.Option(
            "--shortcuts-only",
            help="Install shortcuts only for this package name. Can be used several times.",
        ),
    ] = None,
    # Networking Options
    use_index_cache: Annotated[
        bool,
        typer.Option(
            "-C",
            "--use-index-cache",
            help="Use cache of channel index files, even if it has expired.",
        ),
    ] = False,
    insecure: Annotated[
        bool,
        typer.Option(
            "-k",
            "--insecure",
            help="Allow conda to perform insecure SSL connections and transfers.",
        ),
    ] = False,
    offline: OfflineOption = False,
    # Output, Prompt, and Flow Control Options
    json: JsonOption = False,
    console: Annotated[
        str | None,
        typer.Option(
            "--console",
            help="Select the backend to use for normal output rendering.",
        ),
    ] = None,
    verbose: Annotated[
        int,
        typer.Option(
            "-v",
            "--verbose",
            count=True,
            help="Can be used multiple times. Once for detailed output, twice for INFO logging, etc.",
        ),
    ] = 0,
    quiet: QuietOption = False,
    dry_run: DryRunOption = False,
    yes: YesOption = False,
    download_only: DownloadOnlyOption = False,
    show_channel_urls: ShowChannelUrlsOption = None,
) -> int:
    """
    Create a new conda environment from a list of specified packages.

    To use the newly-created environment, use 'conda activate envname'.
    This command requires either the -n NAME or -p PREFIX option.

    Examples:

        Create an environment containing the package 'sqlite':

            $ cx create -n myenv sqlite

        Create an environment as a clone of an existing environment:

            $ cx create -n env2 --clone env1
    """
    # Import the execute function from the original implementation
    from ..cli.main_create import execute
    from ..common.constants import NULL

    # Validate that name or prefix is provided
    if not name and not prefix:
        typer.echo("Error: Either --name or --prefix is required", err=True)
        raise typer.Exit(1)

    # Create an argparse-compatible Namespace
    args = Namespace(
        packages=packages or [],
        name=name if not prefix else None,
        prefix=prefix if not name else None,
        clone=clone,
        file=file or [],
        dev=1 if dev else NULL,
        # Channel customization
        channel=channel or [],
        use_local=use_local,
        override_channels=override_channels,
        repodata_fns=repodata_fn or NULL,
        experimental=experimental.split(",") if experimental else NULL,
        no_lock=no_lock if no_lock else NULL,
        repodata_use_zst=repodata_use_zst if repodata_use_zst is not None else NULL,
        subdir=subdir or NULL,
        platform=subdir,  # platform is an alias for subdir
        # Solver mode modifiers
        strict_channel_priority=strict_channel_priority
        if strict_channel_priority
        else NULL,
        channel_priority=NULL if not no_channel_priority else "disabled",
        no_deps=no_deps,
        only_deps=only_deps,
        no_pin=no_pin,
        no_default_packages=no_default_packages,
        solver=solver or context.solver,
        # Package linking options
        copy=copy,
        no_shortcuts=no_shortcuts if no_shortcuts else NULL,
        shortcuts_only=shortcuts_only or NULL,
        # Networking options
        use_index_cache=use_index_cache if use_index_cache else NULL,
        insecure=insecure if insecure else NULL,
        offline=offline if offline else NULL,
        # Output options
        json=json,
        console=console or NULL,
        verbosity=verbose,
        quiet=quiet,
        dry_run=dry_run,
        yes=yes,
        download_only=download_only,
        show_channel_urls=show_channel_urls if show_channel_urls is not None else NULL,
        cmd="create",
    )

    context.__init__(argparse_args=args)
    # Call the original execute function
    exit_code = execute(args, None)

    return exit_code if isinstance(exit_code, int) else 0
