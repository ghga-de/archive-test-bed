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

"""Step definitions for unhappy submission of metadata with the data-steward-kit"""


import subprocess
from pathlib import Path

from ..conftest import JointFixture, given, parse, scenarios, then, when

scenarios("../features/unhappy/50_submit_metadata.feature")


@given("we have an unhappy research metadata JSON file")
def unhappy_metadata_json_exist(fixtures: JointFixture):
    unhappy_metadata_path = fixtures.dsk.config.unhappy_metadata_path
    assert unhappy_metadata_path.exists()


@when(
    parse('"{name}" metadata is submitted to the submission store'),
    target_fixture="completed_submit",
)
def submit_with_unhappy_asset(
    name: str, metadata_config_path: Path, fixtures: JointFixture
):
    workdir = fixtures.dsk.config.unhappy_submission_registry
    metadata_json_path = fixtures.dsk.config.metadata_dir / f"{name}_metadata.json"

    completed_submit = (
        subprocess.run(  # nosec B607, B603 pylint: disable=subprocess-run-check
            [
                "ghga-datasteward-kit",
                "metadata",
                "submit",
                "--submission-title",
                "Unhappy Submission",
                "--submission-description",
                "Unhappy Submission Description",
                "--metadata-path",
                metadata_json_path,
                "--config-path",
                metadata_config_path,
            ],
            capture_output=True,
            encoding="utf-8",
            text=True,
            timeout=10 * 60,
            cwd=workdir,
        )
    )

    return completed_submit


@then(parse('I get the expected error for submission with unhappy "{asset}"'))
def check_submission_error(asset: str, completed_submit: subprocess.CompletedProcess):
    expected_errors = {
        "config": [
            "ValidationError: 1 validation error for MetadataConfig",
            "workflow_config -> embed_public",
            "field required (type=value_error.missing)",
        ],
        "model": [
            "MetadataModelAssumptionError: A Submission class is required but does not exist."
        ],
        "metadata": [
            "MetadataValidationError: Validation failed due to following issues: in field",
            "'data_access_committees' is a required property",
        ],
    }

    for msg in expected_errors[asset]:
        assert msg in completed_submit.stderr
