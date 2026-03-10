# Copyright (C) 2012 Anaconda, Inc
# SPDX-License-Identifier: BSD-3-Clause
"""Fixtures for channel priority testing with controlled local channels."""

from __future__ import annotations

from pathlib import Path
from shutil import copy2
from typing import TYPE_CHECKING

import pytest

from conda.common.serialize import json
from conda.common.url import path_to_url

if TYPE_CHECKING:
    from collections.abc import Iterator

    from conda.testing.fixtures import PathFactoryFixture

TEST_RECIPES = Path(__file__).parent / "data" / "test-recipes" / "noarch"


@pytest.fixture
def priority_test_channels(
    path_factory: PathFactoryFixture,
) -> Iterator[tuple[str, str]]:
    """
    Create two local file:// channels for testing channel priority behavior.

    Returns:
        Tuple of (defaults_like_url, conda_forge_like_url)

    The channels contain:
    - defaults-like: priority-base, priority-dep, priority-lib at version 1.0.0
    - conda-forge-like: priority-base, priority-dep, priority-lib at version 2.0.0
    """
    # Create temporary channel directories
    base_dir = path_factory(name="priority_channels")
    base_dir.mkdir()

    defaults_like = base_dir / "defaults-like"
    conda_forge_like = base_dir / "conda-forge-like"

    # Setup channel structure (noarch only, since our packages are noarch)
    for channel_dir in [defaults_like, conda_forge_like]:
        noarch = channel_dir / "noarch"
        noarch.mkdir(parents=True)

    # Copy v1.0.0 packages to defaults-like
    v1_packages = [
        "priority-base-1.0.0-h8f222bd_0.tar.bz2",
        "priority-dep-1.0.0-h8f222bd_0.tar.bz2",
        "priority-lib-1.0.0-h8f222bd_0.tar.bz2",
    ]
    defaults_noarch = defaults_like / "noarch"
    for pkg in v1_packages:
        copy2(TEST_RECIPES / pkg, defaults_noarch / pkg)

    # Copy v2.0.0 packages to conda-forge-like
    v2_packages = [
        "priority-base-2.0.0-h9365bbd_0.tar.bz2",
        "priority-dep-2.0.0-h9365bbd_0.tar.bz2",
        "priority-lib-2.0.0-h9365bbd_0.tar.bz2",
    ]
    conda_forge_noarch = conda_forge_like / "noarch"
    for pkg in v2_packages:
        copy2(TEST_RECIPES / pkg, conda_forge_noarch / pkg)

    # Generate repodata.json for each channel
    for channel_dir, packages in [
        (defaults_like, v1_packages),
        (conda_forge_like, v2_packages),
    ]:
        noarch = channel_dir / "noarch"
        repodata = {"info": {"subdir": "noarch"}, "packages": {}}

        # Create repodata entries
        for pkg_file in packages:
            # Parse filename: priority-base-1.0.0-h8f222bd_0.tar.bz2
            parts = pkg_file.replace(".tar.bz2", "").rsplit("-", 2)
            name = parts[0]
            version = parts[1]
            build = parts[2]

            # Determine dependencies
            depends = []
            if name in ["priority-base", "priority-dep"]:
                depends = ["priority-lib"]

            # Get file size
            pkg_path = noarch / pkg_file
            size = pkg_path.stat().st_size

            repodata["packages"][pkg_file] = {
                "name": name,
                "version": version,
                "build": build,
                "build_number": 0,
                "depends": depends,
                "noarch": "generic",
                "subdir": "noarch",
                "size": size,
            }

        (noarch / "repodata.json").write_text(json.dumps(repodata, sort_keys=True))

    # Convert to file:// URLs
    defaults_url = path_to_url(str(defaults_like))
    conda_forge_url = path_to_url(str(conda_forge_like))

    yield defaults_url, conda_forge_url
