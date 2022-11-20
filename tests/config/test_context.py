# Copyright (C) 2012 Anaconda, Inc
# SPDX-License-Identifier: BSD-3-Clause
from conda.config.context import create_context


def test_happy_path(tmp_path, base_condarc):
    """
    Makes sure that we can parse a correctly written condarc file
    """
    condarc_file = tmp_path / ".condarc"
    condarc_file.write_text(base_condarc)
    context = create_context(extra_config_files=(condarc_file,))

    assert context.channels == ("defaults", "http://localhost")
    assert context.channel_parameters == ("defaults", {"http://localhost": {"fetch_type": "blah"}})

    assert context.always_yes is True
    assert context.changeps1 is False


def test_happy_path_with_aliases(tmp_path, base_condarc_using_alias):
    """
    Makes sure that we can parse a correctly written condarc file when using aliases
    instead of the normal field value.
    """
    condarc_file = tmp_path / ".condarc"
    condarc_file.write_text(base_condarc_using_alias)
    context = create_context(extra_config_files=(condarc_file,))

    assert context.channels == ("defaults", "http://localhost")
    assert context.channel_parameters == ("defaults", {"http://localhost": {"fetch_type": "blah"}})

    assert context.always_yes is True
    assert context.changeps1 is False


def test_reading_from_environment_variables(base_condarc_using_env_vars):
    """
    Make sure that we can read from environment variables correctly, especially variables
    with a special delimiter value.
    """
    context = create_context()

    assert context.pinned_packages == ("test_1", "test_2", "test_3")
    assert context.channels == ("defaults", "localhost", "testing")
    assert context.envs_dirs == ("/home/test", "/var/lib/test")
