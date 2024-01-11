# Copyright 2021 - 2023 Universität Tübingen, DKFZ, EMBL, and Universität zu Köln
# for the German Human Genome-Phenome Archive (GHGA)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


"""Fixture for using HashiCorp vault"""

import hvac
from pydantic import BaseModel
from pytest import fixture

from fixtures.config import Config


class VaultConfig:
    """Class with vault configuration"""

    def __init__(self, config: Config):
        self.url = config.vault_url
        self.token = config.vault_token
        self.path = config.vault_path


class VaultFixture:
    """Vault fixture"""

    def __init__(self, config: VaultConfig):
        self.config = config

    @property
    def client(self) -> hvac.Client:
        return hvac.Client(self.config.url, self.config.token)

    @property
    def keys(self):
        return self.client.secrets.kv.v2.list_secrets(
            path=self.config.path,
        )["data"]["keys"]


@fixture(name="vault", scope="session")
def vault_fixture(config):
    """Pytest fixture for tests using vault."""
    vault_config = VaultConfig(config)
    yield VaultFixture(vault_config)
