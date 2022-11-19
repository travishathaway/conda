# Copyright (C) 2012 Anaconda, Inc
# SPDX-License-Identifier: BSD-3-Clause
import pytest

from conda.auxlib.ish import dals


BASE_CONDARC = """
channels:
    - defaults
    - http://localhost:
        fetch_type: blah
always_yes: yes
changeps1: no
"""


@pytest.fixture()
def base_condarc():
    yield BASE_CONDARC
