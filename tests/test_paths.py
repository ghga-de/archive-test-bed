# Copyright 2021 - 2023 Universität Tübingen, DKFZ, EMBL, and Universität zu Köln
# for the German Human Genome-Phenome Archive (GHGA)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""A test dummy just to make the CI pass."""

from datetime import timedelta

import httpx
import nest_asyncio
import pytest
from ghga_datasteward_kit.cli.metadata import submit, transform
from ghga_datasteward_kit.file_ingest import IngestConfig, file_ingest
from ghga_service_commons.utils.utc_dates import now_as_utc

from src.utils import data_steward_upload_file
from tests.fixtures import (  # noqa: F401 # pylint: disable=unused-import
    JointFixture,
    auth_fixture,
    config_fixture,
    joint_fixture,
    kafka_fixture,
    mongodb_fixture,
    s3_fixture,
    submission_workdir,
)
from tests.fixtures.file import (  # noqa: F401 # pylint: disable=unused-import
    batch_create_file_fixture,
    file_fixture,
)
from tests.fixtures.metadata import (  # noqa: F401 # pylint: disable=unused-import
    SubmissionConfig,
    submission_config_fixture,
)


@pytest.mark.asyncio
async def test_ars(fixtures: JointFixture):
    """Standalone test for the access request service.

    Checks that an access request can be made and notifications are sent out.
    """
    headers = fixtures.auth.generate_headers(
        id_="user-id-doe", name="John Doe", email="doe@home.org", title="Dr."
    )
    date_now = now_as_utc()
    data = {
        "user_id": "user-id-doe",
        "dataset_id": "some-dataset",
        "email": "john@doe.org",
        "request_text": "Can I access some dataset?",
        "access_starts": date_now.isoformat(),
        "access_ends": (date_now + timedelta(days=365)).isoformat(),
    }
    url = "http://ars:8080/access-requests"

    response = httpx.post(url, data=data)
    assert response.status_code == 403

    async with fixtures.kafka.record_events(in_topic="notifications") as event_recorder:
        response = httpx.post(url, headers=headers, json=data)
        assert response.status_code == 201

    assert (
        sum(
            1
            for event in event_recorder.recorded_events
            if event.type_ == "notification"
        )
        == 2
    )


def test_upload_submission(
    workdir,
    fixtures: JointFixture,
    submission_config: SubmissionConfig,
):
    """Test submission via DSKit with configured file object,
       expected to run through without errors

    This test case is not async at the moment because in submit workflow
    asyncio.run() is called by metldata dependency.
    """

    submit(
        submission_title="Test Submission",
        submission_description="Test Submission Description",
        metadata_path=submission_config.metadata_path,
        config_path=submission_config.metadata_config_path,
    )

    assert (workdir / submission_config.submission_store).exists()

    transform(
        config_path=submission_config.metadata_config_path,
    )


@pytest.mark.asyncio
async def test_upload_file_ingest(
    workdir,
    fixtures: JointFixture,
    batch_file_fixture,
    submission_config: SubmissionConfig,
):
    nest_asyncio.apply()
    # FIXME workaround for submit workflow trying to call asyncio.run()
    # within an already running event loop (asyncio-based test case)

    file_objects = batch_file_fixture
    file_metadata_dir = workdir / "file_uploads"
    file_metadata_dir.mkdir()

    submit(
        submission_title="Test Submission",
        submission_description="Test Submission Description",
        metadata_path=submission_config.metadata_path,
        config_path=submission_config.metadata_config_path,
    )

    # transform(
    #     config_path=submission_config.metadata_config_path,
    # )

    ingest_config = IngestConfig(
        file_ingest_url=fixtures.config.file_ingest_url,
        file_ingest_pubkey=fixtures.config.file_ingest_pubkey,
        input_dir=file_metadata_dir,
        submission_store_dir=workdir / submission_config.submission_store,
    )

    for file_object in file_objects:
        metadata_file_path = await data_steward_upload_file(
            file_object=file_object,
            config=fixtures.config,
            file_metadata_dir=file_metadata_dir,
        )
        assert metadata_file_path.exists()

        file_ingest(
            in_path=metadata_file_path,
            token=fixtures.auth.read_token(),
            config=ingest_config,
        )
