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

"""Fixture for testing code that uses the Kafka-based provider."""

from typing import AsyncGenerator

from hexkit.providers.akafka.provider import KafkaEventPublisher
from hexkit.providers.akafka.testutils import KafkaFixture
from kafka import KafkaAdminClient
from pytest_asyncio import fixture as async_fixture

from src.config import Config

__all__ = ["kafka_fixture", "KafkaFixture"]


def delete_topics(kafka_servers: list[str], topics_to_be_deleted: list[str]):
    """Delete given topic from Kafka broker"""
    admin_client = KafkaAdminClient(bootstrap_servers=kafka_servers)
    admin_client.delete_topics(topics_to_be_deleted)


@async_fixture
async def kafka_fixture(config: Config) -> AsyncGenerator[KafkaFixture, None]:
    """Pytest fixture for tests depending on the Kafka-based provider."""

    async with KafkaEventPublisher.construct(config=config) as publisher:
        yield KafkaFixture(
            config=config, kafka_servers=config.kafka_servers, publisher=publisher
        )

    # Delete all topics used by services. This process deletes the messages as
    # the topics will be recreated by the default config.
    delete_topics(
        kafka_servers=config.kafka_servers,
        topics_to_be_deleted=config.service_kafka_topics,
    )
