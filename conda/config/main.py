# Copyright (C) 2012 Anaconda, Inc
# SPDX-License-Identifier: BSD-3-Clause
import abc
import enum
import json
import logging
from argparse import Namespace
from pathlib import Path
from typing import Any, Callable, Sequence

import ruamel.yaml as yaml

from .condarc import get_condarc_obj, CondarcConfig

logger = logging.getLogger(__name__)


class ConfigFileTypes(enum.Enum):
    yaml = "yaml"
    json = "json"


def _yaml_safe():
    parser = yaml.YAML(typ="safe", pure=True)
    parser.indent(mapping=2, offset=2, sequence=4)
    parser.default_flow_style = False
    return parser


def read_yaml_file(path: Path) -> dict[str, Any]:
    """Opens yaml file and returns value dictionary"""
    try:
        with path.open("rb") as file_handle:
            parser = _yaml_safe()
            return parser.load(file_handle)
    except yaml.YAMLError as exc:
        logger.error(exc)


def read_json_file(path: Path) -> dict[str, Any]:
    """Opens json file and returns value dictionary"""
    try:
        with path.open("rb") as file_handle:
            return json.load(file_handle)
    except json.JSONDecodeError as exc:
        logger.error(exc)


ConfigFileParserFunc = Callable[[Path], dict[str, Any]]


def get_config_file_parser(file_type: ConfigFileTypes) -> ConfigFileParserFunc:
    if file_type == ConfigFileTypes.yaml:
        return read_yaml_file


class ConfigSource(abc.ABC):
    @abc.abstractmethod
    def get_parameter(self, name) -> Any:
        """Retrieves the named parameter from the configuration implementation"""
        ...

    @abc.abstractmethod
    def has_parameter(self, name) -> Any:
        """Determines whether the underlying storage object actually has this parameter"""
        ...


class ConfigFileSource(ConfigSource):
    #: Type of file to parse
    file_type: ConfigFileTypes

    #: Parser that gets set from reading the ``file_type``
    file_parser: ConfigFileParserFunc

    #: List of configuration files to parse
    config_files: Sequence[Path]

    #: Object holding merged data from config files
    data: CondarcConfig

    def __init__(self, file_type: ConfigFileTypes, config_files: Sequence[Path]):
        """
        Creates a ConfigFileSource object that holds all the available config files.

        :param file_type: Determines the type of file parser that we set for this object
        :param config_files: List of a files to read configuration from. Order in which the files
                             are listed determines their relative importance (first ones overwrite
                             others).
        """
        self.file_type = file_type
        self.file_parser = get_config_file_parser(file_type)
        self.config_files = config_files
        self.data = self._merge(config_files)

    def _merge(self, config_files: Sequence[Path]) -> CondarcConfig:
        if len(config_files) == 0:
            return CondarcConfig()
        return get_condarc_obj(config_files, self.file_parser)

    def get_parameter(self, name) -> Any:
        return getattr(self.data, name)

    def has_parameter(self, name) -> bool:
        return hasattr(self.data, name)


class CLIConfigSource(ConfigSource):
    """
    The primary purpose of this class is providing a consistent interface
    for our configuration sources.
    """

    #: This is the Namespace class from the argparse module
    args_obj: Namespace

    def __init__(self, args_obj: Namespace):
        """
        Sets the "args_obj" attribute. In the future this could also support different
        types of command line parsers (e.g. click or docopt)
        """
        self.args_obj = args_obj

    def get_parameter(self, name) -> Any:
        return getattr(self.args_obj, name)

    def has_parameter(self, name) -> bool:
        return hasattr(self.args_obj, name)
