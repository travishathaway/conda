# Copyright (C) 2012 Anaconda, Inc
# SPDX-License-Identifier: BSD-3-Clause
from __future__ import annotations

import sys
from contextlib import contextmanager
from io import StringIO
from logging import DEBUG, NOTSET, WARN, getLogger
from types import SimpleNamespace
from typing import TYPE_CHECKING

import pytest

from conda import reporters
from conda.common.io import (
    CaptureTarget,
    attach_stderr_handler,
    captured,
)
from conda.plugins import CondaReporterBackend, CondaReporterOutput
from conda.plugins.types import ReporterRendererBase

if TYPE_CHECKING:
    from pytest import CaptureFixture


def test_captured():
    stdout_text = "stdout text"
    stderr_text = "stderr text"

    def print_captured(*args, **kwargs):
        with captured(*args, **kwargs) as c:
            print(stdout_text, end="")
            print(stderr_text, end="", file=sys.stderr)
        return c

    c = print_captured()
    assert c.stdout == stdout_text
    assert c.stderr == stderr_text

    c = print_captured(CaptureTarget.STRING, CaptureTarget.STRING)
    assert c.stdout == stdout_text
    assert c.stderr == stderr_text

    c = print_captured(stderr=CaptureTarget.STDOUT)
    assert c.stdout == stdout_text + stderr_text
    assert c.stderr is None

    caller_stdout = StringIO()
    caller_stderr = StringIO()
    c = print_captured(caller_stdout, caller_stderr)
    assert c.stdout is caller_stdout
    assert c.stderr is caller_stderr
    assert caller_stdout.getvalue() == stdout_text
    assert caller_stderr.getvalue() == stderr_text

    with captured() as outer_c:
        inner_c = print_captured(None, None)
    assert inner_c.stdout is None
    assert inner_c.stderr is None
    assert outer_c.stdout == stdout_text
    assert outer_c.stderr == stderr_text


def test_attach_stderr_handler():
    name = "abbacadabba"
    logr = getLogger(name)
    assert len(logr.handlers) == 0
    assert logr.level is NOTSET

    debug_message = "debug message 1329-485"

    with captured() as c:
        attach_stderr_handler(WARN, name)
        logr.warn("test message")
        logr.debug(debug_message)

    assert len(logr.handlers) == 1
    assert logr.handlers[0].name == "stderr"
    assert logr.handlers[0].level is WARN
    assert logr.level is NOTSET
    assert c.stdout == ""
    assert "test message" in c.stderr
    assert debug_message not in c.stderr

    # round two, with debug
    with captured() as c:
        attach_stderr_handler(DEBUG, name)
        logr.warn("test message")
        logr.debug(debug_message)
        logr.info("info message")

    assert len(logr.handlers) == 1
    assert logr.handlers[0].name == "stderr"
    assert logr.handlers[0].level is DEBUG
    assert logr.level is NOTSET
    assert c.stdout == ""
    assert "test message" in c.stderr
    assert debug_message in c.stderr


class DummyReporterRenderer(ReporterRendererBase):
    def list(self, data, **kwargs) -> str:
        return f"list: {data}"

    def table(self, data: dict[str, str | int | bool], **kwargs) -> str:
        return f"table: {data}"


@contextmanager
def dummy_io():
    yield sys.stdout


def test_reporters_rendeer(capsys: CaptureFixture):
    """
    Ensure basic coverage of the :class:`~conda.common.io.ReporterManager` class.
    """
    # Setup
    reporter_backend = CondaReporterBackend(
        name="test-reporter-backend", description="test", renderer=DummyReporterRenderer
    )
    reporter_output = CondaReporterOutput(
        name="test-reporter-output", description="test", stream=dummy_io
    )
    plugin_manager = SimpleNamespace(
        get_reporter_backend=lambda _: reporter_backend,
        get_reporter_output=lambda _: reporter_output,
    )
    reporters = ({"backend": "test-reporter-backend", "output": "test-reporter-output"},)

    context = SimpleNamespace(plugin_manager=plugin_manager, reporters=reporters)

    # Test simple rendering of object
    reporters.render("test-string")

    stdout, stderr = capsys.readouterr()
    assert stdout == "test-string"
    assert not stderr

    # Test rendering of object with a style
    reporters.render("test-string", style="envs_list")

    stdout, stderr = capsys.readouterr()
    assert stdout == "envs_list: test-string"
    assert not stderr

    # Test error when style cannot be found
    with pytest.raises(
        AttributeError,
        match="'non_existent_view' is not a valid reporter backend style",
    ):
        reporters.render({"test": "data"}, style="non_existent_view")
