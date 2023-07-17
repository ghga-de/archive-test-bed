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

from .conftest import (
    Config,
    ConnectorFixture,
    S3Fixture,
    async_fixture,
    given,
    scenarios,
)

scenarios("../features/32_download_files.feature")


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
