# Copyright (C) 2012 Anaconda, Inc
# SPDX-License-Identifier: BSD-3-Clause
from __future__ import annotations

from .base.context import context


def render(data, reporters, style: str | None = None, **kwargs) -> None:
    """
    Glues together the configured ``ReporterBackend`` and ``ReporterOutput``
    instances as configured in the reporters setting.
    """
    for settings in context.reporters:
        reporter = context.plugin_manager.get_reporter_backend(settings.get("backend"))
        output = context.plugin_manager.get_reporter_output(settings.get("output"))

        if reporter is None or output is None:
            continue

        renderer = reporter.renderer()

        if style is None:
            style_callback = getattr(renderer, "default")
        else:
            style_callback = getattr(renderer, style, None)
            if style_callback is None:
                raise AttributeError(
                    f"'{style}' is not a valid reporter backend style"
                )

        with output.stream() as file:
            file.write(style_callback(data, **kwargs))
