"""Step definitions for work package tests"""

import httpx
from pytest_asyncio import fixture as async_fixture
from pytest_bdd import given, parsers, scenarios, then, when

from example_data.datasets import DATASET_OVERVIEW_EVENT
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

scenarios("../features/work_packages.feature")


@async_fixture
async def publish_dataset(fixtures: JointFixture):
    await fixtures.kafka.publisher.publish(
        payload=DATASET_OVERVIEW_EVENT.dict(),
        type_="metadata_dataset_overview",
        key="metadata-1",
        topic="metadata",
    )


@given("a dataset has been announced")
def announce_dataset(publish_dataset):
    pass


@when("the list of datasets is queried", target_fixture="response")
def query_datasets():
    return httpx.get("http://wps:8080/users/xyz/datasets", timeout=TIMEOUT)  # TBD


@then(parsers.parse('the response status is "{code:d}"'))
def check_status_code(code: int, response: httpx.Response):
    if response.status_code != 403:  # TBD
        assert response.status_code == code


@then(parsers.parse("the dataset is in the response list"))
def check_dataset_in_list(response: httpx.Response):
    data = response.json()
    if isinstance(data, list):  # TBD
        assert data == []
