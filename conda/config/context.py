# Copyright (C) 2012 Anaconda, Inc
# SPDX-License-Identifier: BSD-3-Clause
from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from typing import Sequence, Any

from .main import ConfigSource, CLIConfigSource, EnvConfigSource, ConfigFileSource, ConfigFileTypes
from .system import SystemConfiguration


class Context:
    """
    This object is meant to be defined as a singleton within this application
    and contains all configuration parameters for the application. These configuration
    parameters come from the following sources:

    - Environment variables
    - CLI arguments/options
    - Configuration files (i.e. ``condarc`` files)
    - System level configuration provided by the SystemConfiguration object
    """

    #: Sequence holding all the different "ConfigSource" objects (i.e. classes that implement this
    #: abstract base class)
    _config_sources: Sequence[ConfigSource]

    #: SystemConfiguration object that holds specific information about the operating system
    #: and other environment specific things (e.g. prefix, conda environment name)
    _system_config: SystemConfiguration

    def __init__(self, system_config: SystemConfiguration, config_sources: Sequence[ConfigSource]):
        """
        Creates the object responsible for gathering all application configuration.
        """
        self._config_sources = config_sources
        self._system_config = system_config

    def __getattr__(self, item):
        raise AttributeError(f"'{self.__class__.__name__}' has no attribute '{item}'")

    def __getattribute__(self, item) -> Any:
        """
        Overrides the default __getattribute__ which allows for searching the ConfigSource
        type objects and the SystemConfiguration object for the correct value to return.

        The order in which the ConfigSource objects are passed in reflects their relative
        importance. The first variable definition we find is returned. We check the
        SystemConfiguration object last for variable definitions.
        """
        # This ensures we avoid special dunder attributes like ``__name__``
        if item.startswith("__"):
            return super().__getattribute__(item)

        config_sources = super().__getattribute__("_config_sources")
        system_config = super().__getattribute__("_system_config")

        for config in config_sources:
            has_param = config.has_parameter(item)
            if has_param:
                value = config.get_parameter(item)
                return value

        if hasattr(system_config, item):
            return getattr(system_config, item)

        raise AttributeError(f"'{self.__class__.__name__}' has no attribute '{item}'")


def create_context(
    args_obj: Namespace | None = None, extra_config_files: tuple[Path, ...] = None
) -> Context:
    """
    This function is responsible for constructing our Context object. It first collects
    configuration from a variety of sources and then uses the Context object to combine
    them all.

    :param args_obj: Namespace object that is created after parsing CLI arguments
    :param extra_config_files: Extra files, other than standard system locations, we want
                               to include
    """
    system_config = SystemConfiguration()  # TODO: should we create this here?
    config_files = system_config.valid_condarc_files

    if extra_config_files is not None:
        config_files += extra_config_files

    config_file_sources = ConfigFileSource(ConfigFileTypes.yaml, config_files)
    env_config_source = EnvConfigSource()
    args_obj = args_obj or Namespace()
    cli_config_source = CLIConfigSource(args_obj)

    # This tuple reflects the order of importance for parsing configuration parameters
    config_sources = (env_config_source, cli_config_source, config_file_sources)

    return Context(system_config, config_sources)
