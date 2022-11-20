# Copyright (C) 2012 Anaconda, Inc
# SPDX-License-Identifier: BSD-3-Clause
import os

import pytest


BASE_CONDARC = """
channels:
    - defaults
    - http://localhost:
        fetch_type: blah
always_yes: yes
changeps1: no
"""

BASE_CONDARC_USING_ALIAS = """
channel:
    - defaults
    - http://localhost:
        fetch_type: blah
yes: yes
changeps1: no
"""


@pytest.fixture()
def base_condarc():
    yield BASE_CONDARC


@pytest.fixture()
def base_condarc_using_alias():
    yield BASE_CONDARC_USING_ALIAS


@pytest.fixture()
def base_condarc_using_env_vars():
    old_env = os.environ

    os.environ = {
        "CONDA_CHANNELS": "defaults,localhost,testing",
        "CONDA_PINNED_PACKAGES": "test_1&test_2&test_3",
        "CONDA_ENVS_DIRS": "/home/test:/var/lib/test",
    }

    yield

    os.environ = old_env
