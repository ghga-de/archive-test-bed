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

""" Utilities for tests """

from pathlib import Path

from ghga_datasteward_kit.s3_upload import Config as S3Config
from ghga_datasteward_kit.s3_upload import async_main as s3_upload
from hexkit.providers.s3.testutils import FileObject

from src.config import Config


async def data_steward_upload_file(
    temp_file: FileObject, config: Config, test_dir: Path
) -> Path:
    """Populate the storage with configured file object, return metadata file path"""
    await s3_upload(
        input_path=temp_file.file_path,
        alias=temp_file.object_id,
        config=S3Config(
            **{
                "s3_endpoint_url": config.s3_endpoint_url,
                "s3_access_key_id": config.s3_access_key_id,
                "s3_secret_access_key": config.s3_secret_access_key,
                "bucket_id": temp_file.bucket_id,
                "part_size": 1024,
                "output_dir": test_dir,
            }
        ),
    )

    return test_dir / f"{temp_file.object_id}.json"
