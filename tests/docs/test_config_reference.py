# Copyright (C) 2012 Anaconda, Inc
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for the pure-Python part of the ``conda_config_reference`` Sphinx extension."""

from __future__ import annotations

import importlib.util
import os
import sys
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from frozendict import frozendict

from conda.base.context import context

if TYPE_CHECKING:
    from types import ModuleType

EXTENSION = (
    Path(__file__).parents[2]
    / "docs"
    / "source"
    / "_extensions"
    / "conda_config_reference.py"
)


@pytest.fixture(scope="module")
def ext(monkeypatch_module: pytest.MonkeyPatch) -> ModuleType:
    pytest.importorskip("sphinx")
    spec = importlib.util.spec_from_file_location("conda_config_reference", EXTENSION)
    module = importlib.util.module_from_spec(spec)
    # dataclasses resolve string annotations through sys.modules
    monkeypatch_module.setitem(sys.modules, spec.name, module)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def monkeypatch_module():
    with pytest.MonkeyPatch.context() as mp:
        yield mp


@pytest.fixture(scope="module")
def grouped(ext: ModuleType) -> dict:
    return ext.build_records(overrides=ext.load_overrides())


def documented_names() -> list[str]:
    return [
        name
        for category, names in context.category_map.items()
        if category not in ("CLI-only", "Hidden and Undocumented")
        for name in names
    ]


def test_every_documented_setting_appears_once(grouped: dict):
    names = [r.name for records in grouped.values() for r in records]
    assert sorted(names) == sorted(documented_names())
    assert len(names) == len(set(names))


def test_hidden_categories_are_skipped(grouped: dict):
    assert "CLI-only" not in grouped
    assert "Hidden and Undocumented" not in grouped


def test_shipped_overrides_are_valid(ext: ModuleType, grouped: dict):
    assert ext.validate_records(grouped, ext.load_overrides()) == []


def test_deprecated_settings_sort_last(grouped: dict):
    for records in grouped.values():
        flags = [r.deprecated for r in records]
        assert flags == sorted(flags)
        live = [r.name for r in records if not r.deprecated]
        assert live == sorted(live)


@pytest.mark.parametrize("name", ["experimental", "report_errors"])
def test_deprecated_settings_are_flagged(grouped: dict, name: str):
    records = {r.name: r for rs in grouped.values() for r in rs}
    assert records[name].deprecated


@pytest.mark.parametrize(
    "name,env_vars,delimiter,from_env",
    [
        ("channel_priority", ("CONDA_CHANNEL_PRIORITY",), None, True),
        ("envs_dirs", ("CONDA_ENVS_DIRS", "CONDA_ENVS_PATH"), os.pathsep, True),
        ("pinned_packages", ("CONDA_PINNED_PACKAGES",), "&", True),
        ("custom_channels", ("CONDA_CUSTOM_CHANNELS",), None, False),
    ],
)
def test_environment_variables(
    grouped: dict,
    name: str,
    env_vars: tuple[str, ...],
    delimiter: str | None,
    from_env: bool,
):
    record = {r.name: r for rs in grouped.values() for r in rs}[name]
    assert record.env_vars == env_vars
    assert record.settable_from_env is from_env
    assert record.string_delimiter == delimiter


@pytest.mark.parametrize(
    "name,expected",
    [
        ("channel_priority", "strict | flexible | disabled"),
        ("channels", "list[str]"),
        ("custom_multichannels", "map[str, list[str]]"),
        ("ssl_verify", "str | bool"),
    ],
)
def test_type_labels(grouped: dict, name: str, expected: str):
    record = {r.name: r for rs in grouped.values() for r in rs}[name]
    assert record.type_label == expected


class Color(Enum):
    red = "red"


@pytest.mark.parametrize(
    "value,expected",
    [
        (None, "null"),
        (True, "true"),
        (False, "false"),
        (0, "0"),
        ("", '""'),
        ("base", "base"),
        ((), "[]"),
        (("a", "b"), "[a, b]"),
        (frozendict(), "{}"),
        (frozendict({"a": "b"}), "{a: b}"),
        (Color.red, "red"),
    ],
)
def test_format_default(ext: ModuleType, value: object, expected: str):
    assert ext.format_default(value) == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        ("One. Two.", "One."),
        ("Use e.g. this. Then that.", "Use e.g. this."),
        ("No period", "No period"),
        ("First line\ncontinues here. Next.", "First line continues here."),
        ("Para one.\n\nPara two.", "Para one."),
    ],
)
def test_first_sentence(ext: ModuleType, text: str, expected: str):
    assert ext.first_sentence(text) == expected


def test_first_sentence_truncates(ext: ModuleType):
    result = ext.first_sentence("word " * 100, max_length=20)
    assert len(result) == 20
    assert result.endswith("…")


def test_validate_reports_unknown_override_and_key(ext: ModuleType, grouped: dict):
    problems = ext.validate_records(
        grouped, {"nope": {"example": "x"}, "channels": {"bogus": 1}}
    )
    assert any("unknown setting 'nope'" in p for p in problems)
    assert any("unknown key 'bogus'" in p for p in problems)


def test_validate_reports_duplicate_label(ext: ModuleType, grouped: dict):
    overrides = {"channels": {"labels": ["x"]}, "json": {"labels": ["x"]}}
    records = {r.name: r for rs in grouped.values() for r in rs}
    for name, override in overrides.items():
        records[name].override = override
    try:
        problems = ext.validate_records(grouped, overrides)
    finally:
        for name in overrides:
            records[name].override = {}
    assert any("label 'x'" in p for p in problems)


def test_render_setting_includes_fields(ext: ModuleType, grouped: dict):
    record = {r.name: r for rs in grouped.values() for r in rs}["envs_dirs"]
    source = "\n".join(ext.render_setting(record))
    assert ".. confval:: envs_dirs" in source
    assert ":Aliases: ``envs_path``" in source
    assert "``CONDA_ENVS_DIRS``, ``CONDA_ENVS_PATH``" in source
    assert ".. conda-config-markdown::" in source


def test_render_setting_marks_unsupported_environment_variable(
    ext: ModuleType, grouped: dict
):
    record = {r.name: r for rs in grouped.values() for r in rs}["custom_channels"]
    assert ":Environment variable: not supported" in "\n".join(
        ext.render_setting(record)
    )
