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

"""Fixture for clean up after test run."""

import os
import shutil

import pytest_asyncio
from hexkit.providers.mongodb.provider import MongoDbDaoFactory

from src.config import Config

__all__ = ["cleanup_fixture"]


@pytest_asyncio.fixture(name="cleanup_fixture")
async def cleanup_fixture(fixtures, config: Config):
    """Clean up fixture that execute cleanup logic after test run"""
    yield

    # Remove temporary test data directory
    await remove_test_data_dir(config)

    # Empty all storage buckets
    for bucket_id in [
        config.inbox_bucket,
        config.outbox_bucket,
        config.staging_bucket,
        config.permanent_bucket,
    ]:
        await empty_storage_bucket(fixtures.s3, bucket_id)

    # Drop all mongodb collections in service databases
    for db_name in config.service_db_names:
        config_dict = config.dict()
        config_dict["db_name"] = db_name  # Update config to connect service database
        await drop_mongo_collections(Config(**config_dict))


async def remove_test_data_dir(config: Config):
    """Remove temporary test data directory"""
    test_data_dir = config.test_dir
    if os.path.exists(test_data_dir):
        shutil.rmtree(test_data_dir)


async def empty_storage_bucket(s3_fixture, bucket_id: str):
    """Clean the test artifacts or files from given bucket"""

    # Get list of all object in bucket
    object_ids = await s3_fixture.storage.list_all_object_ids(bucket_id=bucket_id)

    # Delete all objects
    for object_id in object_ids:
        await s3_fixture.storage.delete_object(bucket_id=bucket_id, object_id=object_id)


async def drop_mongo_collections(config: Config):
    """Drop all mongodb collections in given database"""
    dao_factory = MongoDbDaoFactory(config=config)
    collections = await dao_factory._db.list_collection_names()
    for collection in collections:
        await dao_factory._db.drop_collection(name_or_collection=collection)
