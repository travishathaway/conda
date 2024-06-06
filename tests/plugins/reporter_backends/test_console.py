# Copyright (C) 2012 Anaconda, Inc
# SPDX-License-Identifier: BSD-3-Clause
from conda.plugins.reporter_backends.console import ConsoleReporterRenderer


def test_console_reporter_renderer():
    """
    Tests the ConsoleReporterRenderer class
    """
    test_data = {"one": "value_one", "two": "value_two", "three": "value_three"}
    test_str = "a string value"
    expected_table_str = (
        "\n   one : value_one\n   two : value_two\n three : value_three\n\n"
    )
    renderer = ConsoleReporterRenderer()

    assert renderer.table(test_data) == expected_table_str
    assert renderer.default(test_str) == test_str
