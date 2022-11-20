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
