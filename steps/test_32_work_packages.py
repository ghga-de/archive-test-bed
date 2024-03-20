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

"""Step definitions for creating work package tests in the frontend"""

from .conftest import (
    Config,
    JointFixture,
    MongoFixture,
    Response,
    StateStorage,
    given,
    parse,
    scenarios,
    then,
    when,
)

scenarios("../features/32_work_packages.feature")


@given("no work packages have been created yet")
def wps_database_is_empty(config: Config, mongo: MongoFixture, state: StateStorage):
    if config.use_api_gateway:
        # black-box testing: cannot empty service database
        assert not state.get_state("dataset to be downloaded")
        assert not state.get_state("all files to be downloaded")
        assert not state.get_state("vcf files to be downloaded")
        assert not state.get_state("download token for all files")
        assert not state.get_state("download token for vcf files")
        return
    mongo.empty_databases(config.wps_db_name, exclude_collections="datasets")
    state.unset_state("download token for")
    state.unset_state("dataset to be downloaded")
    state.unset_state("files to be downloaded")


@given("the test datasets have been announced")
def announce_dataset(config: Config, mongo: MongoFixture):
    if config.use_api_gateway:
        # black-box testing: cannot look into service database
        return
    datasets = mongo.wait_for_documents(config.wps_db_name, "datasets", {}, number=2)
    assert datasets
    assert len(datasets) == 6
    titles = {dataset["title"][4:-8] for dataset in datasets}
    assert titles == {"A", "B", "C", "D", "complete-A", "complete-B"}


@when(parse('"{full_name}" lists the datasets'), target_fixture="response")
def query_datasets_with_wps(fixtures: JointFixture, full_name: str):
    session = fixtures.auth.get_session(name=full_name, state_store=fixtures.state)
    assert session
    headers = fixtures.auth.headers(session=session) if session else {}
    user_id = session.user_id
    url = f"{fixtures.config.wps_url}/users/{user_id}/datasets"
    return fixtures.http.get(url, headers=headers)


@then(parse('only the test dataset "{dataset_char}" is returned'))
def check_dataset_in_list(
    dataset_char: str, fixtures: JointFixture, response: Response
):
    data = response.json()
    assert isinstance(data, list) and len(data) == 1
    dataset = data[0]
    assert isinstance(dataset, dict)
    assert dataset.get("stage") == "download"
    assert dataset.get("title") == f"The complete-{dataset_char} dataset"
    files = dataset.get("files")
    assert files and isinstance(files, list)
    fixtures.state.set_state("dataset to be downloaded", f"DS_{dataset_char}")


@when(
    parse(
        '"{full_name}" creates a work package for "{file_scope}" files in test dataset'
    ),
    target_fixture="response",
)
def create_work_package(
    full_name: str, fixtures: JointFixture, response: Response, file_scope: str
):
    data = response.json()
    assert isinstance(data, list) and len(data) == 1
    dataset = data[0]
    assert isinstance(dataset, dict)
    dataset_id = dataset.get("id")
    assert dataset_id
    files = dataset.get("files")
    assert files and isinstance(files, list)

    if file_scope == "all":
        file_ids = None
    elif file_scope in ["vcf", "fastq"]:
        extension = f".{file_scope}.gz"
        files = [file for file in files if file["extension"] == extension]
        file_ids = [file["id"] for file in files]
    else:
        raise ValueError("Unknown file_scope {file_scope}")

    fixtures.state.set_state(f"{file_scope} files to be downloaded", files)

    data = {
        "dataset_id": dataset_id,
        "type": "download",
        "file_ids": file_ids,
        "user_public_crypt4gh_key": fixtures.config.user_public_crypt4gh_key,
    }
    url = f"{fixtures.config.wps_url}/work-packages"

    session = fixtures.auth.get_session(name=full_name, state_store=fixtures.state)
    assert session
    headers = fixtures.auth.headers(session=session) if session else {}
    return fixtures.http.post(url, headers=headers, json=data)


@then(parse('the response contains a download token for "{file_scope}" files'))
def check_download_token(fixtures: JointFixture, response: Response, file_scope: str):
    data = response.json()
    assert set(data) == {"id", "token"}
    id_, token = data["id"], data["token"]
    assert 20 <= len(id_) < 40 and 80 < len(token) < 120
    id_and_token = f"{id_}:{token}"
    fixtures.state.set_state(
        f"download token for {file_scope} files",
        id_and_token,
    )
