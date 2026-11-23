# Copyright (C) 2012 Anaconda, Inc
# SPDX-License-Identifier: BSD-3-Clause
from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass

import pytest

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
from conda.plugins.types import ReporterRendererBase


@dataclass(frozen=True)
class SampleEvent(Event):
    value: int = 0


def test_event_is_frozen():
    event = SampleEvent(value=1)
    with pytest.raises(FrozenInstanceError):
        event.value = 2  # type: ignore[misc]


EVENT_CASES = [
    ("render_data", RenderDataEvent, {"data": 1}),
    ("render_detail_view", DetailViewEvent, {"data": {"a": "b"}}),
    ("render_envs_list", EnvsListEvent, {"prefixes": ("/env",)}),
    ("render_spinner_start", SpinnerStartEvent, {"message": "m"}),
    ("render_spinner_end", SpinnerEndEvent, {"message": "m", "success": True}),
    ("render_fetch_section_start", FetchSectionStartEvent, {}),
    (
        "render_fetch_task_start",
        FetchTaskStartEvent,
        {"task_id": 1, "name": "n", "version": "1"},
    ),
    (
        "render_fetch_task_progress",
        FetchTaskProgressEvent,
        {"task_id": 1, "fraction": 0.5},
    ),
    ("render_fetch_task_end", FetchTaskEndEvent, {"task_id": 1, "success": True}),
    ("render_fetch_section_end", FetchSectionEndEvent, {"success": True}),
]


@pytest.mark.parametrize("_,event_type,kwargs", EVENT_CASES)
def test_event_types_are_frozen_events(_, event_type, kwargs):
    event = event_type(**kwargs)

    assert isinstance(event, Event)
    with pytest.raises(FrozenInstanceError):
        event.new_attribute = None  # type: ignore[attr-defined]


def test_event_defaults():
    assert RenderDataEvent(data=1).style is None
    assert not EnvsListEvent(prefixes=()).show_size
    assert SpinnerStartEvent(message="m").fail_message == "failed\n"
    assert FetchTaskStartEvent(task_id=1, name="n", version="1").size is None


@pytest.mark.parametrize("method,event_type,kwargs", EVENT_CASES)
def test_renderer_base_render_methods_default_to_noop(method, event_type, kwargs):
    class Renderer(ReporterRendererBase):
        detail_view = envs_list = progress_bar = spinner = prompt = None  # type: ignore[assignment]

    assert getattr(Renderer(), method)(event_type(**kwargs)) is None
