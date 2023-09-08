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

"""Step definitions for unhappy uploading and ingesting files with the datasteward-kit"""

import json
import os
import shutil
import subprocess

from ghga_datasteward_kit.file_ingest import IngestConfig

from fixtures.file import FileObject
from steps.test_12_upload_files import call_data_steward_kit_upload
from steps.utils import ingest_config_as_file, temporary_file, upload_config_as_file

from ..conftest import DskFixture, JointFixture, given, parse, scenarios, then, when

scenarios("../features/unhappy/52_upload_files.feature")


@given("we have no unhappy file metadata")
def reset_unhappy_file_metadata(dsk: DskFixture):
    unhappy_file_metadata_dir = (
        dsk.config.unhappy_submission_registry / dsk.config.file_metadata_dir
    )

    if os.path.exists(unhappy_file_metadata_dir):
        shutil.rmtree(unhappy_file_metadata_dir)


@when(
    parse("the files for the minimal metadata are uploaded individually"),
    target_fixture="file_object_upload",
)
def upload_files_individually(
    fixtures: JointFixture, unhappy_file_fixture: list[FileObject]
) -> tuple[FileObject, subprocess.CompletedProcess]:
    file_metadata_dir = (
        fixtures.dsk.config.unhappy_submission_registry
        / fixtures.dsk.config.file_metadata_dir
    )
    file_metadata_dir.mkdir(exist_ok=True)

    file_object = unhappy_file_fixture[0]

    upload_config_path = upload_config_as_file(
        config=fixtures.config, file_metadata_dir=file_metadata_dir
    )

    completed_upload = (
        subprocess.run(  # nosec B607, B603 pylint: disable=subprocess-run-check
            [
                "ghga-datasteward-kit",
                "files",
                "upload",
                "--alias",
                file_object.object_id,
                "--input-path",
                str(file_object.file_path),
                "--config-path",
                upload_config_path,
            ],
            capture_output=True,
            encoding="utf-8",
            text=True,
            timeout=60,
        )
    )

    return file_object, completed_upload


@when(
    parse("the files for the unhappy metadata are uploaded individually"),
    target_fixture="unhappy_file_objects",
)
def upload_unhappy_files_individually(
    fixtures: JointFixture, unhappy_file_fixture: list[FileObject]
) -> list[FileObject]:
    unhappy_file_metadata_dir = (
        fixtures.dsk.config.unhappy_submission_registry
        / fixtures.dsk.config.file_metadata_dir
    )
    unhappy_file_metadata_dir.mkdir(exist_ok=True)

    for file_object in unhappy_file_fixture:
        call_data_steward_kit_upload(
            file_object=file_object,
            config=fixtures.config,
            file_metadata_dir=unhappy_file_metadata_dir,
        )

    return unhappy_file_fixture


@when(
    "the unhappy file metadata is ingested", target_fixture="completed_unhappy_ingest"
)
def ingest_unhappy_file_metadata(fixtures: JointFixture) -> subprocess.CompletedProcess:
    unhappy_file_metadata_dir = (
        fixtures.dsk.config.unhappy_submission_registry
        / fixtures.dsk.config.file_metadata_dir
    )
    # Use happy submission registry for a valid submission
    submission_store = (
        fixtures.dsk.config.submission_registry / fixtures.dsk.config.submission_store
    )
    ingest_config = IngestConfig(
        file_ingest_url=fixtures.config.file_ingest_url,
        file_ingest_pubkey=fixtures.config.file_ingest_pubkey,
        input_dir=unhappy_file_metadata_dir,
        submission_store_dir=submission_store,
        map_files_fields=fixtures.dsk.config.metadata_file_fields,
    )

    ingest_config_path = ingest_config_as_file(config=ingest_config)
    dsk_token_path = fixtures.config.dsk_token_path
    token = fixtures.auth.read_simple_token()

    with temporary_file(dsk_token_path, token) as _:
        completed_unhappy_ingest = (
            subprocess.run(  # nosec B607, B603 pylint: disable=subprocess-run-check
                [
                    "ghga-datasteward-kit",
                    "files",
                    "ingest-upload-metadata",
                    "--config-path",
                    ingest_config_path,
                ],
                capture_output=True,
                encoding="utf-8",
                text=True,
                timeout=10 * 60,
            )
        )

        return completed_unhappy_ingest


@then("the file metadata for each uploaded unhappy file exists")
def metadata_files_exist(
    fixtures: JointFixture, unhappy_file_objects: list[FileObject]
):
    """Check that the file metadata exists."""
    file_metadata_dir = (
        fixtures.dsk.config.unhappy_submission_registry
        / fixtures.dsk.config.file_metadata_dir
    )
    for file_object in unhappy_file_objects:
        metadata_file_path = file_metadata_dir / f"{file_object.object_id}.json"
        assert metadata_file_path.exists()


@then("I get the expected existing file error")
def check_existing_file_error(
    file_object_upload: tuple[FileObject, subprocess.CompletedProcess]
):
    file_object = file_object_upload[0]
    completed_upload = file_object_upload[1]

    expected_error = (
        "CRITICAL:s3_upload:Output file "
        f"/tmp/unhappy_submission/file_metadata/{file_object.object_id}.json "
        "already exists and cannot be overwritten.\n"
    )

    assert "CRITICAL" in completed_upload.stderr
    assert expected_error in completed_upload.stderr


@then("I get the expected accession not found error")
def check_accession_not_found_error(
    fixtures: JointFixture, completed_unhappy_ingest: subprocess.CompletedProcess
):
    metadata = json.loads(fixtures.dsk.config.unhappy_metadata_path.read_text())

    file_alias = metadata["study_files"][0]["alias"]
    expected_error = f"No accession exists for file alias {file_alias}"

    assert expected_error in completed_unhappy_ingest.stdout
