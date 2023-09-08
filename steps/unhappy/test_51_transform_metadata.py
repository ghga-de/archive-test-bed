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

"""Step definitions for unhappy transformation of metadata with the data-steward-kit"""


import glob
import json
import os
import subprocess
from pathlib import Path

from ..conftest import TIMEOUT, JointFixture, given, parse, scenarios, then, when

scenarios("../features/unhappy/51_transform_metadata.feature")


@given("we have an unhappy submission JSON file in the local submission store")
def unhappy_submission_json_exist(fixtures: JointFixture):
    submission_store = (
        fixtures.dsk.config.unhappy_submission_registry
        / fixtures.dsk.config.submission_store
    )
    assert submission_store.exists()
    json_files = glob.glob(os.path.join(submission_store, "*.json"))
    assert len(json_files) == 1
    submission_json = Path(json_files[0])
    submission = json.loads(submission_json.read_text(encoding="utf-8"))
    assert not submission["content"]


@when(
    "unhappy metadata submission is transformed", target_fixture="completed_transform"
)
def transform_metadata(metadata_config_path: Path, fixtures: JointFixture):
    workdir = fixtures.dsk.config.unhappy_submission_registry

    completed_transform = (
        subprocess.run(  # nosec B607, B603 pylint: disable=subprocess-run-check
            [
                "ghga-datasteward-kit",
                "metadata",
                "transform",
                "--config-path",
                str(metadata_config_path),
            ],
            capture_output=True,
            encoding="utf-8",
            text=True,
            timeout=TIMEOUT * 60,
            cwd=workdir,
        )
    )

    assert not completed_transform.stdout
    assert "ERROR" not in completed_transform.stderr
    # dskit transform doesn't return an ERROR, even when the submission store is empty

    return completed_transform


@then(parse('I get the expected error for transformation with unhappy "{asset}"'))
def check_transformation_error(
    asset: str, completed_transform: subprocess.CompletedProcess
):
    expected_errors = {
        "config": [
            "ValidationError: 1 validation error for MetadataConfig",
            "workflow_config -> embed_public",
            "field required (type=value_error.missing)",
        ],
        "model": [
            "MetadataModelAssumptionError: A Submission class is required but does not exist."
        ],
    }

    for msg in expected_errors[asset]:
        assert msg in completed_transform.stderr


@then("the source_events are empty")
def source_events_are_empty(fixtures: JointFixture):
    source_events = (
        fixtures.dsk.config.unhappy_submission_registry
        / fixtures.dsk.config.event_store
        / fixtures.dsk.config.source_events
    )
    assert source_events.is_dir()
    assert not any(source_events.iterdir())
