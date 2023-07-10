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

import httpx
from pytest_asyncio import fixture as async_fixture

from example_data.datasets import DATASET_OVERVIEW_EVENT

from .conftest import (
    TIMEOUT,
    WPS_DB_NAME,
    WPS_URL,
    JointFixture,
    LoginFixture,
    MongoFixture,
    given,
    parse,
    scenarios,
    then,
    when,
)

scenarios("../features/work_packages.feature")


@async_fixture
async def publish_dataset(fixtures: JointFixture):
    await fixtures.kafka.publisher.publish(
        payload=DATASET_OVERVIEW_EVENT.dict(),
        type_="metadata_dataset_overview",
        key="metadata-1",
        topic="metadata",
    )


@given("no work packages have been created yet")
def wps_database_is_empty(mongo: MongoFixture):
    mongo.empty_database(WPS_DB_NAME)


@given("the test dataset has been announced")
def announce_dataset(publish_dataset):
    pass


@when("the list of datasets is queried", target_fixture="response")
def query_datasets(login: LoginFixture):
    user_id = login.user["_id"]
    return httpx.get(
        f"{WPS_URL}/users/{user_id}/datasets", headers=login.headers, timeout=TIMEOUT
    )


@then(parse("the test dataset is in the response list"))
def check_dataset_in_list(response: httpx.Response):
    data = response.json()
    dataset = DATASET_OVERVIEW_EVENT
    files = DATASET_OVERVIEW_EVENT.files
    assert data == [
        {
            "id": dataset.accession,
            "description": dataset.description,
            "stage": dataset.stage.value,
            "title": dataset.title,
            "files": [
                {"id": file.accession, "extension": file.file_extension}
                for file in files
            ],
        }
    ]
