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

""" Metadata related  fixture """

import base64
import os
import shutil
import tempfile
from pathlib import Path
from typing import Generator

from pydantic import BaseSettings
from pytest import fixture

BASE_DIR = Path(__file__).parent.parent
TMP_DIR = Path(tempfile.gettempdir())


def private_keyfile_content(raw_key: str):
    """Create content for unencrypted Crypt4GH private key file from raw encoded key."""
    magic_word = b"c4gh-v1"
    none = b"\x00\x04none"
    kdf = cipher = none
    comment = b""
    key_bytes = base64.b64decode(raw_key)
    content_bytes = magic_word + kdf + cipher + key_bytes + comment
    content = base64.b64encode(content_bytes).decode("ascii")
    return content


class ConnectorConfig(BaseSettings):
    """Config for metadata and related submissions"""

    work_dir: Path = TMP_DIR / "connector"
    user_public_key_path: Path = work_dir / "key.pub"
    user_private_key_path: Path = work_dir / "key.sec"
    download_dir: Path = work_dir / "download"


class ConnectorFixture:
    """GHGA Connector fixture"""

    config: ConnectorConfig

    def __init__(self, config: ConnectorConfig):
        self.config = config

    def reset_work_dir(self):
        """Reset the working director for the GHGA connector."""
        work_dir = self.config.work_dir

        if os.path.exists(work_dir):
            shutil.rmtree(work_dir)

        work_dir.mkdir()
        self.config.download_dir.mkdir()

    def store_keys(self, public_key: str, private_key: str):
        """Store the given public and private keys in the working directory."""
        with open(self.config.user_public_key_path, "w", encoding="ascii") as file:
            file.write("-----BEGIN CRYPT4GH PUBLIC KEY-----\n")
            file.write(public_key)
            file.write("\n-----END CRYPT4GH PUBLIC KEY-----")
        with open(self.config.user_private_key_path, "w", encoding="ascii") as file:
            file.write("-----BEGIN CRYPT4GH PRIVATE KEY-----\n")
            file.write(private_keyfile_content(private_key))
            file.write("\n-----END CRYPT4GH PRIVATE KEY-----")


@fixture(name="connector")
def connector_fixture() -> Generator[ConnectorFixture, None, None]:
    """Pytest fixture for tests using the GHGA Connector."""
    config = ConnectorConfig()
    yield ConnectorFixture(config=config)
