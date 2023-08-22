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

import hashlib
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, List, Optional

import httpx
import yaml
from ghga_datasteward_kit.file_ingest import IngestConfig
from ghga_datasteward_kit.loading import LoadConfig
from hexkit.custom_types import JsonObject

from fixtures.config import Config

TIMEOUT = 10

DATASET_OVERVIEW_KEYS = {"accession", "title", "description"}
FILE_OVERVIEW_KEYS = {
    "accession",
    "checksum",
    "checksum_type",
    "format",
    "name",
    "size",
}


@contextmanager
def temporary_file(file_path, content):
    """Yield the temporary file with required content"""
    try:
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(content)
        yield file_path
    finally:
        os.remove(file_path)


def write_data_to_yaml(data: dict[str, str], file_path=None):
    if not file_path:
        _, file_path = tempfile.mkstemp()  # pylint: disable=consider-using-with

    with open(file_path, "w", encoding="utf-8") as file_:
        yaml.dump(data, file_)

    return file_path


def ingest_config_as_file(config: IngestConfig):
    """Create upload config file for data steward kit files ingest-upload-metadata"""

    ingest_config = {
        "file_ingest_url": config.file_ingest_url,
        "file_ingest_pubkey": config.file_ingest_pubkey,
        "submission_store_dir": str(config.submission_store_dir),
        "input_dir": str(config.input_dir),
        "map_files_fields": config.map_files_fields,
    }

    return write_data_to_yaml(data=ingest_config)


def load_config_as_file(config: LoadConfig):
    """Create upload config file for data steward kit files load"""

    load_config = {
        "event_store_path": str(config.event_store_path),
        "artifact_topic_prefix": config.artifact_topic_prefix,
        "artifact_types": config.artifact_types,
        "loader_api_root": config.loader_api_root,
    }

    return write_data_to_yaml(data=load_config)


def upload_config_as_file(config: Config, file_metadata_dir: Path):
    """Create upload config file for data steward kit files upload"""

    upload_config = {
        "s3_endpoint_url": config.s3_endpoint_url,
        "s3_access_key_id": config.s3_access_key_id,
        "s3_secret_access_key": config.s3_secret_access_key.get_secret_value(),
        "bucket_id": config.staging_bucket,
        "part_size": str(config.part_size),
        "output_dir": str(file_metadata_dir),
    }

    return write_data_to_yaml(data=upload_config)


def get_ext_char(file_path: Path):
    """Get file path and return first character of the extension"""
    first_char = " "
    if file_path.suffixes:
        first_char = file_path.suffixes[0].strip(".")[0]
    return first_char


def verify_named_file(
    target_dir: Path,
    name: str,
    extension: str,
    encrypted=False,
    checksum: Optional[str] = None,
    size_in_bytes: Optional[int] = None,
) -> None:
    """Verify a file with given parameters"""

    file_path = target_dir
    name += extension
    if encrypted:
        name += ".c4gh"

    matching = [path for path in file_path.iterdir() if path.name == name]
    assert len(matching) == 1, f"File {name} was not found"

    if not encrypted:
        file_path = matching[0]

        if size_in_bytes:
            file_size_in_bytes = os.path.getsize(file_path)
            assert file_size_in_bytes == size_in_bytes

        if checksum:
            with open(file_path, "rb") as file:
                file_checksum = calculate_checksum(file.read())
            assert file_checksum == checksum


def search_dataset_rpc(
    config: Config,
    filters: Optional[List[Dict[str, str]]] = None,
    query: Optional[str] = None,
    class_name: str = "EmbeddedDataset",
    limit: Optional[int] = None,
    skip: Optional[int] = None,
):
    """Send a search request to the MASS"""

    search_parameters: JsonObject = {
        "class_name": class_name,
        **{
            key: value
            for key, value in {
                "limit": limit,
                "query": query,
                "skip": skip,
                "filters": filters,
            }.items()
            if value is not None
        },
    }
    url = f"{config.mass_url}/rpc/search"
    return httpx.post(url, json=search_parameters, timeout=TIMEOUT)


def get_dataset_overview(content: dict) -> dict:
    """Condense a dataset content dict to a dataset overview dict."""
    simplified = {}
    files = {}
    for key, value in content.items():
        if key in DATASET_OVERVIEW_KEYS:
            simplified[key] = value
        elif key.endswith("_files"):
            for file_ in value:
                alias = file_.pop("alias")
                files[alias] = {
                    key: value
                    for key, value in file_.items()
                    if key in FILE_OVERVIEW_KEYS
                }
    simplified["files"] = files
    return simplified


def calculate_checksum(file_contents: bytes) -> str:
    """Compute the SHA256 hash of a file."""
    return hashlib.sha256(file_contents).hexdigest()
