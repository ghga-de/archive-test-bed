# Copyright 2021 - 2023 Universität Tübingen, DKFZ, EMBL, and Universität zu Köln
# for the German Human Genome-Phenome Archive (GHGA)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""Step definitions for transforming metadata via the data-steward-kit"""

import os
import subprocess
from pathlib import Path

from .conftest import JointFixture, scenarios, then, when

scenarios("../features/11_transform_metadata.feature")


def call_data_steward_kit_transform(
    metadata_config_path: Path,
    timeout: int = 1800,  # this command may take more than 15 min
):
    """Call cli command 'ghga-datasteward-kit metadata transform'
    to run the transformation workflow on submitted metadata
    """
    completed_transform = subprocess.run(  # nosec B607, B603
        [
            "ghga-datasteward-kit",
            "metadata",
            "transform",
            "--config-path",
            str(metadata_config_path),
        ],
        capture_output=True,
        check=True,
        encoding="utf-8",
        text=True,
        timeout=timeout,
    )

    assert not completed_transform.stdout
    assert "ERROR" not in completed_transform.stderr


@when("submitted metadata is transformed")
def transform_metadata(fixtures: JointFixture):
    workdir = fixtures.dsk.config.submission_registry
    cwd = os.getcwd()
    os.chdir(workdir)
    call_data_steward_kit_transform(
        metadata_config_path=fixtures.dsk.config.metadata_config_path
    )
    os.chdir(cwd)


@then("the embedded_public event exists")
def embedded_public_event_exists(fixtures: JointFixture):
    assert fixtures.dsk.config.embedded_public_event.exists()
