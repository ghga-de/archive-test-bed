"""Step definitions for work package tests"""

from datetime import timedelta
from typing import Sequence

import httpx
from ghga_service_commons.utils.utc_dates import now_as_utc
from hexkit.providers.akafka.testutils import EventRecorder, RecordedEvent
from pytest_asyncio import fixture as async_fixture
from pytest_bdd import given, parsers, scenarios, then, when

from tests.fixtures import (  # noqa: F401
    JointFixture,
    auth_fixture,
    config_fixture,
    joint_fixture,
    kafka_fixture,
    mongodb_fixture,
    s3_fixture,
)

TIMEOUT = 10

scenarios("../features/access_request.feature")


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


@given(parsers.parse('I am logged in as "{name}"'), target_fixture="headers")
def access_as_user(name: str, fixtures: JointFixture) -> dict[str, str]:
    if name.startswith(("Prof. ", "Dr. ")):
        title, name = name.split(None, 1)
    else:
        title = None
    user_id = "id-of-" + name.lower().replace(" ", "-")
    email = name.lower().replace(" ", ".") + "@home.org"
    headers = fixtures.auth.generate_headers(
        id_=user_id, name=name, email=email, title=title
    )
    return headers


@when("I request access to the test dataset", target_fixture="response")
def request_access_for_dataset(headers: dict[str, str], event_recorder):
    assert event_recorder
    url = "http://ars:8080/access-requests"
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


@then(parsers.parse('the response status code is "{code:d}"'))
def check_status_code(code: int, response: httpx.Response):
    assert response.status_code == code


@then(parsers.parse('an email has been sent to "{email}"'))
def check_dataset_in_list(email: str, recorded_events: Sequence[RecordedEvent]):
    assert any(
        event.payload["recipient_email"] == email
        for event in recorded_events
        if event.type_ == "notification"
    )
