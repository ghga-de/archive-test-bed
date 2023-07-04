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


"""Step definitions for work package tests"""

from datetime import timedelta
from typing import Sequence

import httpx
from ghga_service_commons.utils.utc_dates import now_as_utc
from hexkit.providers.akafka.testutils import EventRecorder, RecordedEvent
from pymongo import MongoClient
from pytest_asyncio import fixture as async_fixture
from pytest_bdd import given, parsers, scenarios, then, when

from tests.fixtures import (  # noqa: F401
    Config,
    JointFixture,
    auth_fixture,
    config_fixture,
    joint_fixture,
    kafka_fixture,
    mongodb_fixture,
    s3_fixture,
)

ARS_URL = "http://ars:8080"

TIMEOUT = 10

parse = parsers.parse

scenarios("../features/access_request.feature")


def add_user(config: Config, user: dict):
    """Add user directly to the database.

    This is needed because users are not registered as part of the test,
    and the claims repository checks whether the users exist.
    """
    db_connection_str = config.db_connection_str
    client = MongoClient(str(db_connection_str.get_secret_value()))  # type: MongoClient
    db = client["auth"]
    users = db.get_collection("users")
    user_id = user["_id"]
    users.replace_one({"_id": user_id}, user, upsert=True)
    client.close()


@async_fixture
async def event_recorder(fixtures: JointFixture) -> EventRecorder:
    event_recorder = fixtures.kafka.record_events(in_topic="notifications")
    await event_recorder.start_recording()
    return event_recorder


@async_fixture
async def recorded_events(event_recorder: EventRecorder) -> Sequence[RecordedEvent]:
    try:
        await event_recorder.stop_recording()
    except event_recorder.stop_recording:
        pass
    return event_recorder.recorded_events


@given(parse('I am logged in as "{name}"'), target_fixture="headers")
def access_as_user(name: str, fixtures: JointFixture) -> dict[str, str]:
    if name.startswith(("Prof. ", "Dr. ")):
        title, name = name.split(None, 1)
    else:
        title = None
    user_id = "id-of-" + name.lower().replace(" ", "-")
    ext_id = f"{user_id}@lifescience-ri.eu"
    email = name.lower().replace(" ", ".") + "@home.org"
    role = "data_steward" if "steward" in name.lower() else None
    add_user(
        config=fixtures.config,
        user={
            "_id": user_id,
            "status": "active",
            "name": name,
            "email": email,
            "title": title,
            "ext_id": ext_id,
            "registration_date": 1688472000,
        },
    )
    headers = fixtures.auth.generate_headers(
        id_=user_id, name=name, email=email, title=title, role=role
    )
    return headers


@when("I request access to the test dataset", target_fixture="response")
def request_access_for_dataset(headers: dict[str, str], event_recorder):
    assert event_recorder
    url = f"{ARS_URL}/access-requests"
    date_now = now_as_utc()
    data = {
        "user_id": "id-of-john-doe",
        "dataset_id": "test-dataset-1",
        "email": "john.doe@home.org",
        "request_text": "Can I access the test dataset?",
        "access_starts": date_now.isoformat(),
        "access_ends": (date_now + timedelta(days=365)).isoformat(),
    }
    response = httpx.post(url, headers=headers, json=data)
    return response


@then(parse('the response status code is "{code:d}"'))
def check_status_code(code: int, response: httpx.Response):
    assert response.status_code == code


@then(parse('an email has been sent to "{email}"'))
def check_email_sent_to(email: str, recorded_events: Sequence[RecordedEvent]):
    assert any(
        event.payload["recipient_email"] == email
        for event in recorded_events
        if event.type_ == "notification"
    )


@when("I fetch the list of access requests", target_fixture="response")
def fetch_list_of_access_requests(headers: dict[str, str]):
    url = f"{ARS_URL}/access-requests"
    response = httpx.get(url, headers=headers)
    return response


@then(parse('there is one request for the test dataset from "{name}"'))
def there_is_one_request(name: str, response: httpx.Response):
    requests = response.json()
    requests = [
        request
        for request in requests
        if request["dataset_id"] == "test-dataset-1"
        and request["full_user_name"] == name
    ]
    assert len(requests) == 1


@when(parse('I allow the pending request from "{name}"'), target_fixture="response")
def allow_pending_request(name: str, headers: dict[str, str], response: httpx.Response):
    requests = response.json()
    requests = [
        request
        for request in requests
        if request["dataset_id"] == "test-dataset-1"
        and request["status"] == "pending"
        and request["full_user_name"] == name
    ]
    assert len(requests) == 1
    request = requests[0]
    request_id = request["id"]
    url = f"{ARS_URL}/access-requests/{request_id}"
    data = {"status": "allowed"}
    response = httpx.patch(url, headers=headers, json=data)
    return response


@then(parse('the status of the request from "{name}" is "{status}"'))
def there_are_access_requests(name: str, status: str, response: httpx.Response):
    requests = response.json()
    requests = [
        request
        for request in requests
        if request["dataset_id"] == "test-dataset-1"
        and request["full_user_name"] == name
    ]
    assert len(requests) == 1
    request = requests[0]
    assert request["status"] == status
