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

import json
from datetime import timedelta
from pathlib import Path

import httpx
import pytest
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
)
from tests.fixtures.file import (  # noqa: F401 # pylint: disable=unused-import
    file_fixture,
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


@pytest.mark.asyncio
async def test_data_steward_kit_upload(
    tmp_path: Path, fixtures: JointFixture, temp_file_fixture
):
    """Test file upload via ghga_datasteward_kit with configured file object"""

    temp_file = temp_file_fixture
    metadata_file_path = await data_steward_upload_file(
        temp_file=temp_file, config=fixtures.config, test_dir=tmp_path
    )

    assert metadata_file_path.exists()

    file_uuid = json.loads(metadata_file_path.read_text()).get("File UUID")

    assert await fixtures.s3.storage.does_object_exist(
        bucket_id=fixtures.config.staging_bucket, object_id=file_uuid
    )
