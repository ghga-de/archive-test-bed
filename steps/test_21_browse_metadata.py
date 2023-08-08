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

"""Step definitions for metadata browsing tests"""


import httpx
from hexkit.custom_types import JsonObject

from .conftest import TIMEOUT, Config, scenarios, when

scenarios("../features/21_browse_metadata.feature")


@when("I query documents with invalid class name", target_fixture="response")
def query_with_invalid_class(config: Config):
    search_parameters: JsonObject = {
        "class_name": "InvalidClass",
        "query": "",
        "filters": [],
        "skip": 0,
    }
    url = f"{config.mass_url}/rpc/search"
    return httpx.post(url=url, json=search_parameters, timeout=TIMEOUT)
