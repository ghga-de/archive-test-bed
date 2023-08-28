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

"""Storage fixture for state management between test cases."""

import re
from typing import Any

from pytest import fixture

from fixtures.config import Config
from fixtures.mongo import MongoFixture


class StateStorage:
    """State object for in-memory storage"""

    memory_storage: dict = {}
    config: Config
    mongo: MongoFixture

    def __init__(self, config: Config, mongo: MongoFixture):
        self.config = config
        self.mongo = mongo

    def get_state(self, state_name: str) -> Any:
        if self.config.use_memory_storage:
            return self.memory_storage.get(state_name, None)

        state = self.mongo.find_document("tb", "state", {"_id": state_name})
        return (state or {}).get("value")

    def set_state(self, state_name: str, value: Any):
        if self.config.use_memory_storage:
            self.memory_storage[state_name] = value
        else:
            self.mongo.replace_document(
                "tb", "state", {"_id": state_name, "value": value}
            )

    def unset_state(self, state_regex: str):
        if self.config.use_memory_storage:
            regex = re.compile(state_regex)
            for state_name in self.memory_storage:
                if regex.match(state_name):
                    self.memory_storage.pop(state_name)
        else:
            self.mongo.remove_document("tb", "state", {"_id": {"$regex": state_regex}})

    def reset_state(self):
        if self.config.use_memory_storage:
            self.memory_storage = {}
        else:
            self.mongo.empty_databases("tb")


@fixture(name="state", scope="session")
def state_fixture(config: Config, mongo: MongoFixture) -> StateStorage:
    """Fixture that provides a state storage."""
    return StateStorage(config=config, mongo=mongo)
