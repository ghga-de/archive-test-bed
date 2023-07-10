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

"""Fixtures for the inter service integration tests"""

from typing import NamedTuple

from pytest import fixture

from src.config import Config
from tests.fixtures.auth import TokenGenerator, auth_fixture
from tests.fixtures.c4gh import C4GHKeyPair, c4gh_fixture
from tests.fixtures.kafka import KafkaFixture, kafka_fixture
from tests.fixtures.mongo import MongoFixture, mongo_fixture
from tests.fixtures.s3 import S3Fixture, s3_fixture

__all__ = [
    "auth_fixture",
    "config_fixture",
    "c4gh_fixture",
    "kafka_fixture",
    "mongo_fixture",
    "s3_fixture",
    "joint_fixture",
]


class JointFixture(NamedTuple):
    """Collection of fixtures returned by `joint_fixture`."""

    config: Config
    c4gh: C4GHKeyPair
    kafka: KafkaFixture
    mongo: MongoFixture
    s3: S3Fixture
    auth: TokenGenerator


@fixture(name="config")  # pyright: ignore
def config_fixture() -> Config:
    """Get the testbed configuration."""
    return Config()  # pyright: ignore


# pylint: disable=redefined-outer-name
@fixture(name="fixtures")
def joint_fixture(  # pylint: disable=too-many-arguments
    config: Config,
    c4gh: C4GHKeyPair,
    kafka: KafkaFixture,
    mongo: MongoFixture,
    s3: S3Fixture,
    auth: TokenGenerator,
) -> JointFixture:
    """A fixture that collects all fixtures for integration testing."""

    return JointFixture(config, c4gh, kafka, mongo, s3, auth)
