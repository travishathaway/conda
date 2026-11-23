# Copyright (C) 2012 Anaconda, Inc
# SPDX-License-Identifier: BSD-3-Clause
from __future__ import annotations

from contextlib import nullcontext
from dataclasses import dataclass
from io import StringIO
from typing import TYPE_CHECKING

import pytest

from conda.base.context import context, reset_context
from conda.exceptions import CondaSystemExit, DryRunExit
from conda.plugins.reporter_backends.console import (
    ConsoleReporterRenderer,
    TQDMProgressBar,
)
from conda.plugins.reporter_backends.events import (
    DetailViewEvent,
    EnvsListEvent,
    Event,
    FetchSectionEndEvent,
    FetchSectionStartEvent,
    FetchTaskEndEvent,
    FetchTaskProgressEvent,
    FetchTaskStartEvent,
    RenderDataEvent,
    SpinnerEndEvent,
    SpinnerStartEvent,
)
from conda.plugins.reporter_backends.json import JSONReporterRenderer
from conda.reporters import (
    CondaReporter,
    confirm_yn,
    get_progress_bar,
    get_progress_bar_context_manager,
    get_reporter,
    get_spinner,
    render,
    render_data,
    reset_reporter,
    spinner,
)

if TYPE_CHECKING:
    from pytest import CaptureFixture, MonkeyPatch


def test_render(capsys: CaptureFixture):
    """
    Ensure basic coverage of the :func:`~conda.reporters.render` function.
    """
    # Test simple rendering of object
    with pytest.deprecated_call():
        render("test-string")

    stdout, stderr = capsys.readouterr()
    assert stdout == "test-string\n"
    assert not stderr

    # Test rendering of object with a style
    with pytest.deprecated_call():
        render(["test-string"], style="envs_list")

    stdout, stderr = capsys.readouterr()
    assert "conda environments" in stdout
    assert "test-string" in stdout
    assert not stderr

    # Test error when style cannot be found
    with (
        pytest.deprecated_call(),
        pytest.raises(
            AttributeError,
            match="'non_existent_view' is not a valid reporter backend style",
        ),
    ):
        render({"test": "data"}, style="non_existent_view")


def test_get_progress_bar(monkeypatch):
    """
    Ensure basic coverage of the :func:`~conda.reporters.get_progress_bar~` function
    """
    monkeypatch.setattr("conda.plugins.reporter_backends.console.is_tty", lambda: True)
    monkeypatch.setattr(
        "conda.plugins.reporter_backends.console.term_dumb", lambda: False
    )
    with pytest.deprecated_call():
        progress_bar_manager = get_progress_bar("test")

    assert isinstance(progress_bar_manager, TQDMProgressBar)


def test_get_progress_bar_context_managers():
    """
    Ensure basic coverage of the
    :func:`~conda.reporters.get_progress_bar_context_manager~` function
    """
    with pytest.deprecated_call():
        progress_bar_context_manager = get_progress_bar_context_manager()

    assert isinstance(progress_bar_context_manager, nullcontext)


def test_confirm_yn_dry_run_exit(monkeypatch: MonkeyPatch):
    with pytest.raises(DryRunExit):
        monkeypatch.setenv("CONDA_DRY_RUN", "true")
        reset_context()

        confirm_yn()


def test_confirm_yn_always_yes(monkeypatch: MonkeyPatch):
    monkeypatch.setenv("CONDA_ALWAYS_YES", "true")
    monkeypatch.setenv("CONDA_DRY_RUN", "false")
    reset_context()
    assert context.always_yes
    assert not context.dry_run

    confirm_yn()


def test_confirm_yn_yes(monkeypatch: MonkeyPatch, capsys: CaptureFixture):
    monkeypatch.setattr("sys.stdin", StringIO("blah\ny\n"))

    monkeypatch.setenv("CONDA_ALWAYS_YES", "false")
    monkeypatch.setenv("CONDA_DRY_RUN", "false")
    reset_context()
    assert not context.always_yes
    assert not context.dry_run

    assert confirm_yn()

    stdout, stderr = capsys.readouterr()
    assert "Invalid choice" in stdout


def test_confirm_yn_no(monkeypatch: MonkeyPatch):
    monkeypatch.setattr("sys.stdin", StringIO("n\n"))

    with pytest.raises(CondaSystemExit):
        monkeypatch.setenv("CONDA_ALWAYS_YES", "false")
        monkeypatch.setenv("CONDA_DRY_RUN", "false")
        reset_context()

        assert not context.always_yes
        assert not context.dry_run

        confirm_yn()


@dataclass(frozen=True)
class _UnhandledEvent(Event):
    pass


@pytest.mark.parametrize("event", [Event(), _UnhandledEvent()])
def test_reporter_send_ignores_unhandled_event(mocker, event):
    renderer = mocker.MagicMock()
    CondaReporter(renderer).send(event)

    assert not renderer.method_calls


def test_get_reporter_is_singleton():
    reset_reporter()
    reporter = get_reporter()

    assert isinstance(reporter, CondaReporter)
    assert get_reporter() is reporter

    reset_reporter()
    assert get_reporter() is not reporter


def test_reset_context_resets_reporter():
    reporter = get_reporter()
    reset_context()

    assert get_reporter() is not reporter


@pytest.mark.parametrize(
    "console,renderer_type",
    [("classic", ConsoleReporterRenderer), ("json", JSONReporterRenderer)],
)
def test_get_reporter_uses_configured_backend(
    monkeypatch: MonkeyPatch, console, renderer_type
):
    monkeypatch.setenv("CONDA_CONSOLE", console)
    reset_context()

    assert isinstance(get_reporter()._renderer, renderer_type)


@pytest.mark.parametrize(
    "event,method",
    [
        (RenderDataEvent(data=1), "render_data"),
        (DetailViewEvent(data={"a": "b"}), "render_detail_view"),
        (EnvsListEvent(prefixes=()), "render_envs_list"),
        (SpinnerStartEvent(message="m"), "render_spinner_start"),
        (SpinnerEndEvent(message="m", success=True), "render_spinner_end"),
        (FetchSectionStartEvent(), "render_fetch_section_start"),
        (
            FetchTaskStartEvent(task_id=1, name="n", version="1"),
            "render_fetch_task_start",
        ),
        (FetchTaskProgressEvent(task_id=1, fraction=0.5), "render_fetch_task_progress"),
        (FetchTaskEndEvent(task_id=1, success=True), "render_fetch_task_end"),
        (FetchSectionEndEvent(success=True), "render_fetch_section_end"),
    ],
)
def test_reporter_send_routes_event_to_renderer(mocker, event, method):
    renderer = mocker.MagicMock()
    CondaReporter(renderer).send(event)

    getattr(renderer, method).assert_called_once_with(event)


def test_spinner_sends_start_then_end(mocker):
    reporter = mocker.patch("conda.reporters.get_reporter").return_value

    with spinner("Solving", fail_message="nope\n"):
        pass

    assert [call.args[0] for call in reporter.send.call_args_list] == [
        SpinnerStartEvent(message="Solving", fail_message="nope\n"),
        SpinnerEndEvent(message="Solving", success=True),
    ]


@pytest.mark.parametrize("exc", [ValueError, KeyboardInterrupt])
def test_spinner_reports_failure_and_reraises(mocker, exc):
    reporter = mocker.patch("conda.reporters.get_reporter").return_value

    with pytest.raises(exc), spinner("Solving"):
        raise exc

    assert reporter.send.call_args_list[-1].args[0] == SpinnerEndEvent(
        message="Solving", success=False
    )


@pytest.mark.parametrize(
    "data,style,kwargs,expected",
    [
        ("text", None, {}, RenderDataEvent(data="text")),
        ({"a": "b"}, "detail_view", {}, DetailViewEvent(data={"a": "b"})),
        (["/a", "/b"], "envs_list", {}, EnvsListEvent(prefixes=("/a", "/b"))),
        (
            ("/a",),
            "envs_list",
            {"show_size": True},
            EnvsListEvent(prefixes=("/a",), show_size=True),
        ),
        (
            {"envs": ["/a"], "envs_details": {}},
            "envs_list",
            {},
            RenderDataEvent(data={"envs": ["/a"], "envs_details": {}}),
        ),
    ],
)
def test_render_data_sends_matching_event(mocker, data, style, kwargs, expected):
    reporter = mocker.patch("conda.reporters.get_reporter").return_value

    render_data(data, style, **kwargs)

    reporter.send.assert_called_once_with(expected)


def test_render_data_rejects_unknown_style(mocker):
    mocker.patch("conda.reporters.get_reporter")

    with pytest.raises(AttributeError, match="not a valid reporter backend style"):
        render_data("x", "non_existent_view")


def test_get_spinner_is_deprecated():
    with pytest.deprecated_call(match="conda.reporters.spinner"):
        get_spinner("message")


@pytest.mark.parametrize(
    "console,data,expected",
    [
        ("json", {"a": 1}, '{\n  "a": 1\n}'),
        ("classic", "plain", "plain\n"),
    ],
)
def test_render_data_end_to_end(monkeypatch, capsys, console, data, expected):
    monkeypatch.setenv("CONDA_CONSOLE", console)
    reset_context()

    render_data(data)

    assert capsys.readouterr().out == expected
