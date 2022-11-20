# Copyright (C) 2012 Anaconda, Inc
# SPDX-License-Identifier: BSD-3-Clause
from __future__ import annotations

import warnings
from argparse import Namespace
from collections.abc import Mapping
from pathlib import Path
from typing import Sequence, Any

from .main import ConfigSource, CLIConfigSource, ConfigFileSource, ConfigFileTypes
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

    def __getattr__(self, item) -> Any:
        """
        Overrides the default __getattr__ which allows for searching the ConfigSource
        type objects and the SystemConfiguration object for the additional values to return.
        This is done to make it convenient for us to access all of our configuration
        variables in a single object.

        The order in which the ConfigSource objects are passed in reflects their relative
        importance. The first variable definition we find is returned. We check the
        SystemConfiguration object last for variable definitions.

        Properties and attributes directly defined on the Context object will be returned
        before anything else.
        """
        for config in self._config_sources:
            has_param = config.has_parameter(item)
            if has_param:
                value = config.get_parameter(item)
                return value

        if hasattr(self._system_config, item):
            return getattr(self._system_config, item)

        raise AttributeError(
            f"The following attribute '{item}' was not found on {self.__class__.__name__}, "
            f"{self.__class__.__name__}._config_sources or "
            f"{self.__class__.__name__}._system_config"
        )

    def _get_channel_names(self) -> tuple[str, ...]:
        """
        Channels can be stored as either a string or a mapping where the first and only
        key in this mapping is a channel name.

        Example:
            When we have the following condarc:
            ```
            channels:
              - defaults
              - http://localhost
                  type: local
            ```

            This method will return:
            ```
            ("defaults", "http://localhost")
            ```
        """
        channel_names = []

        for channel in self.__getattr__("channels"):
            if isinstance(channel, Mapping):
                keys = channel.keys()
                if len(keys) > 0:
                    name, *_ = keys
                    channel_names.append(name)
            else:
                channel_names.append(channel)

        return tuple(channel_names)

    @property
    def channels(self):
        return self._get_channel_names()

    @property
    def channel_parameters(self):
        return self.__getattr__("channels")

    @property
    def experimental_solver(self):
        # TODO: Remove in a later release
        warnings.warn(
            "'context.experimental_solver' is pending deprecation and will be removed. "
            "Please consider using 'context.solver' instead.",
            PendingDeprecationWarning,
        )
        return self.__getattr__("solver")


def create_context(
    args_obj: Namespace | None = None, extra_config_files: tuple[Path, ...] = None
) -> Context:
    """
    This function is responsible for constructing our Context object. It first collects
    configuration from a variety of sources and then uses the Context object to combine
    them all.

    :param args_obj: Namespace object that is created after parsing CLI arguments
    :param extra_config_files: Extra files, other than standard system locations, we want
                               to include; these override values from previous files.
    """
    system_config = SystemConfiguration()  # TODO: should we create this here?
    config_files = system_config.valid_condarc_files

    if extra_config_files is not None:
        config_files += extra_config_files

    config_file_sources = ConfigFileSource(ConfigFileTypes.yaml, config_files)
    args_obj = args_obj or Namespace()
    cli_config_source = CLIConfigSource(args_obj)

    # This tuple reflects the order of importance for parsing configuration parameters
    config_sources = (cli_config_source, config_file_sources)

    return Context(system_config, config_sources)
