# Copyright (C) 2012 Anaconda, Inc
# SPDX-License-Identifier: BSD-3-Clause
import re

import pytest

import conda.core.index
from conda.common.io import env_var
from conda.exceptions import PluginError
from conda.base.context import context
from conda.plugins.types import CondaVirtualPackage
from conda.testing.solver_helpers import package_dict
from conda import plugins
from conda.plugins.virtual_packages import cuda


class VirtualPackagesPlugin:
    @plugins.hookimpl
    def conda_virtual_packages(self):
        yield CondaVirtualPackage(
            name="abc",
            version="123",
            build=None,
        )
        yield CondaVirtualPackage(
            name="def",
            version="456",
            build=None,
        )
        yield CondaVirtualPackage(
            name="ghi",
            version="789",
            build="xyz",
        )


@pytest.fixture()
def plugin(plugin_manager):
    plugin = VirtualPackagesPlugin()
    plugin_manager.register(plugin)
    return plugin


def test_invoked(plugin):
    index = conda.core.index.get_reduced_index(
        context.default_prefix,
        context.default_channels,
        context.subdirs,
        (),
        context.repodata_fns[0],
    )

    packages = package_dict(index)

    assert packages["__abc"].version == "123"
    assert packages["__def"].version == "456"
    assert packages["__ghi"].version == "789"
    assert packages["__ghi"].build == "xyz"


def test_duplicated(plugin_manager):
    plugin_manager.register(VirtualPackagesPlugin())
    plugin_manager.register(VirtualPackagesPlugin())

    with pytest.raises(PluginError, match=re.escape("Conflicting `virtual_packages` plugins found")):
        conda.core.index.get_reduced_index(
            context.default_prefix,
            context.default_channels,
            context.subdirs,
            (),
            context.repodata_fns[0],
        )


def test_cuda_detection(clear_cuda_version):
    # confirm that CUDA detection doesn't raise exception
    version = cuda.cuda_version()
    assert version is None or isinstance(version, str)


def test_cuda_override(clear_cuda_version):
    with env_var("CONDA_OVERRIDE_CUDA", "4.5"):
        version = cuda.cached_cuda_version()
        assert version == "4.5"


def test_cuda_override_none(clear_cuda_version):
    with env_var("CONDA_OVERRIDE_CUDA", ""):
        version = cuda.cuda_version()
        assert version is None
