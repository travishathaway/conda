# Copyright (C) 2012 Anaconda, Inc
# SPDX-License-Identifier: BSD-3-Clause
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from conda.testing.integration import package_is_installed

if TYPE_CHECKING:
    from pytest import MonkeyPatch

    from conda.testing.fixtures import CondaCLIFixture, TmpEnvFixture

pytestmark = pytest.mark.usefixtures("parametrized_solver_fixture")


@pytest.mark.integration
@pytest.mark.parametrize(
    "pinned_package",
    [
        pytest.param(True, id="with pinned_package"),
        pytest.param(False, id="without pinned_package"),
    ],
)
def test_reorder_channel_priority(
    tmp_env: TmpEnvFixture,
    monkeypatch: MonkeyPatch,
    conda_cli: CondaCLIFixture,
    priority_test_channels: tuple[str, str],
    pinned_package: bool,
):
    """
    Test channel priority behavior with controlled local packages.

    This test verifies that:
    1. Pinned packages remain on their original channel during update --all
    2. Unpinned packages move to the new channel when a newer version exists
    3. Transient dependencies also move to match their dependents

    Uses locally-controlled test packages to avoid external package changes.
    """
    defaults_url, conda_forge_url = priority_test_channels

    # Package names for testing
    package1 = "priority-base"  # Will be pinned or not based on test parameter
    package2 = "priority-dep"  # Always unpinned
    transient_dep = "priority-lib"  # Should move with its dependents

    # Set pinned package
    if pinned_package:
        monkeypatch.setenv("CONDA_PINNED_PACKAGES", package1)

    # Create environment with v1.0.0 from defaults-like channel
    with tmp_env(
        "--override-channels",
        f"--channel={defaults_url}",
        package1,
        package2,
    ) as prefix:
        # Verify all packages are v1.0.0 from defaults-like channel
        rec1 = package_is_installed(prefix, package1)
        rec2 = package_is_installed(prefix, package2)
        rec_dep = package_is_installed(prefix, transient_dep)

        assert rec1 is not None
        assert rec1.version == "1.0.0"
        assert "defaults-like" in rec1.channel.name

        assert rec2 is not None
        assert rec2.version == "1.0.0"
        assert "defaults-like" in rec2.channel.name

        assert rec_dep is not None
        assert rec_dep.version == "1.0.0"
        assert "defaults-like" in rec_dep.channel.name

        # Update --all with conda-forge-like channel (has v2.0.0)
        conda_cli(
            "update",
            f"--prefix={prefix}",
            "--override-channels",
            f"--channel={conda_forge_url}",
            "--all",
            "--yes",
        )

        # Verify behavior based on pinning
        rec1_after = package_is_installed(prefix, package1)
        rec2_after = package_is_installed(prefix, package2)
        rec_dep_after = package_is_installed(prefix, transient_dep)

        if pinned_package:
            # Pinned package should stay at v1.0.0 from defaults-like
            assert rec1_after.version == "1.0.0"
            assert "defaults-like" in rec1_after.channel.name
        else:
            # Unpinned package should move to v2.0.0 from conda-forge-like
            assert rec1_after.version == "2.0.0"
            assert "conda-forge-like" in rec1_after.channel.name

        # Unpinned package2 should always move to v2.0.0
        assert rec2_after.version == "2.0.0"
        assert "conda-forge-like" in rec2_after.channel.name

        # Transient dependency should move to conda-forge-like
        assert rec_dep_after.version == "2.0.0"
        assert "conda-forge-like" in rec_dep_after.channel.name
