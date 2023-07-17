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

"""Step definitions for file download tests"""

import re
import subprocess

from .conftest import (
    Config,
    ConnectorFixture,
    JointFixture,
    S3Fixture,
    async_fixture,
    get_state,
    given,
    scenarios,
    when,
)

scenarios("../features/32_download_files.feature")

# TBD: the download currently fails because of a DCS issue
SKIP_DOWNLOAD_TEST = True


@async_fixture
async def empty_download_buckets(s3: S3Fixture) -> bool:
    await s3.empty_buckets(["inbox", "staging"])
    return True


@given("the download buckets are empty")
def download_buckets_empty(empty_download_buckets: bool):
    assert empty_download_buckets


@given("I have an empty working directory for the GHGA connector")
def clean_connector_work_dir(connector: ConnectorFixture):
    connector.reset_work_dir()


@given("my Crypt4GH key pair has been stored in two key files")
def keys_are_made_available(connector: ConnectorFixture, config: Config):
    connector.store_keys(
        public_key=config.user_public_crypt4gh_key,
        private_key=config.user_private_crypt4gh_key,
    )


@when("I run the download command of the GHGA connector")
def run_the_download_command(fixtures: JointFixture):
    if SKIP_DOWNLOAD_TEST:
        return
    download_token = get_state("a download token has been created", fixtures.mongo)
    assert download_token and isinstance(download_token, str)
    connector = fixtures.connector
    completed_download = subprocess.run(  # nosec B607, B603
        [
            "ghga-connector",
            "download",
            "--output-dir",
            connector.config.download_dir,
            "--debug",
        ],
        cwd=connector.config.work_dir,
        input=download_token,
        capture_output=True,
        check=True,
        encoding="utf-8",
        text=True,
        timeout=10 * 60,
    )

    assert not completed_download.stdout
    assert not re.search("error|traceback", completed_download.stderr, re.I)
