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

import time
from datetime import timedelta
from pathlib import Path

import httpx
import pytest
from ghga_connector.cli import config as connector_config
from ghga_connector.core.api_calls import get_file_metadata, get_upload_info
from ghga_event_schemas import pydantic_ as event_schemas
from ghga_service_commons.utils.utc_dates import now_as_utc
from hexkit.providers.akafka.testutils import ExpectedEvent, check_recorded_events

from src.config import Config
from src.download_path import decrypt_file, download_file
from src.upload_path import delegate_paths
from tests.fixtures import (  # noqa: F401 # pylint: disable=unused-import
    JointFixture,
    auth_fixture,
    config_fixture,
    joint_fixture,
    kafka_fixture,
    mongo_fixture,
    s3_fixture,
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

    response = httpx.post(url, json=data)
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
async def test_full_path(tmp_path: Path, fixtures: JointFixture):
    """Test up- and download path"""
    unencrypted_id, encrypted_id, unencrypted_data, checksum = await delegate_paths(
        fixtures=fixtures
    )

    await check_upload_path(unencrypted_id=unencrypted_id, encrypted_id=encrypted_id)
    await check_download_path(
        encrypted_id=encrypted_id,
        checksum=checksum,
        output_dir=tmp_path,
        fixtures=fixtures,
    )
    decrypt_and_check(
        encrypted_id=encrypted_id,
        content=unencrypted_data,
        tmp_dir=tmp_path,
        config=fixtures.config,
    )


async def check_upload_path(*, unencrypted_id: str, encrypted_id: str):
    """Check correct state for upload path"""
    await check_upload_status(file_id=unencrypted_id, expected_status="rejected")
    # <= 180 did not work in actions, so let's currently keep it this way
    time.sleep(300)
    await check_upload_status(file_id=encrypted_id, expected_status="accepted")


async def check_upload_status(*, file_id: str, expected_status: str):
    """Assert upload attempt state matches expected state"""
    api_url = connector_config.upload_api
    metadata = get_file_metadata(api_url=api_url, file_id=file_id)
    upload_id = metadata["latest_upload_id"]
    upload_attempt = get_upload_info(api_url=api_url, upload_id=upload_id)
    assert upload_attempt["status"] == expected_status


async def check_download_path(
    *,
    encrypted_id: str,
    checksum: str,
    output_dir: Path,
    fixtures: JointFixture,
):
    """Check correct state for download path"""

    # record download_served event
    async with fixtures.kafka.record_events(
        in_topic="file_downloads"
    ) as event_recorder:
        download_file(
            file_id=encrypted_id, output_dir=output_dir, config=fixtures.config
        )

    # construct expected event
    payload = event_schemas.FileDownloadServed(
        file_id=encrypted_id, decrypted_sha256=checksum, context="unknown"
    ).dict()
    type_ = "download_served"
    key = encrypted_id
    expected_event = ExpectedEvent(payload=payload, type_=type_, key=key)

    # filter for relevant event type
    recorded_events = [
        event for event in event_recorder.recorded_events if event.type_ == type_
    ]

    check_recorded_events(
        recorded_events=recorded_events,
        expected_events=[expected_event, expected_event],
    )


def decrypt_and_check(encrypted_id: str, content: bytes, tmp_dir: Path, config: Config):
    """Decrypt file and compare to original"""

    encrypted_location = tmp_dir / encrypted_id
    decrypted_location = tmp_dir / f"{encrypted_id}_decrypted"

    decrypt_file(
        input_location=encrypted_location,
        output_location=decrypted_location,
        config=config,
    )

    with decrypted_location.open("rb") as dl_file:
        downloaded_content = dl_file.read()

    # cleanup
    encrypted_location.unlink()
    decrypted_location.unlink()

    assert downloaded_content == content
