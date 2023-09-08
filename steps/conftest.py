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

"""Shared steps and fixtures"""

import inspect
from functools import wraps
from typing import Any, NamedTuple

import httpx
from pytest_bdd import (  # noqa: F401; pylint: disable=unused-import
    given,
    parsers,
    scenarios,
    then,
    when,
)

from fixtures import (  # noqa: F401; pylint: disable=unused-import
    Config,
    ConnectorFixture,
    DskFixture,
    JointFixture,
    KafkaFixture,
    MongoFixture,
    S3Fixture,
    auth_fixture,
    batch_file_fixture,
    config_fixture,
    connector_fixture,
    dsk_fixture,
    event_loop,
    file_fixture,
    joint_fixture,
    kafka_fixture,
    mongo_fixture,
    s3_fixture,
    unhappy_file_fixture,
)

TIMEOUT = 10

parse = parsers.parse  # pylint: disable=invalid-name


# Helpers for async step functions


def async_step(step):
    """Decorator that converts an async step function to a normal one."""

    signature = inspect.signature(step)
    parameters = list(signature.parameters.values())
    has_event_loop = any(parameter.name == "event_loop" for parameter in parameters)
    if not has_event_loop:
        parameters.append(
            inspect.Parameter("event_loop", inspect.Parameter.POSITIONAL_OR_KEYWORD)
        )
        step.__signature__ = signature.replace(parameters=parameters)

    @wraps(step)
    def run_step(*args, **kwargs):
        loop = kwargs["event_loop"] if has_event_loop else kwargs.pop("event_loop")
        return loop.run_until_complete(step(*args, **kwargs))

    return run_step


# Shared step functions


class LoginFixture(NamedTuple):
    """A fixture to hold the users and their access tokens."""

    user: dict[str, Any]
    headers: dict[str, str]


@given(parse('I am logged in as "{name}"'), target_fixture="login")
def access_as_user(name: str, fixtures: JointFixture) -> LoginFixture:
    # Create user dictionary
    if name.startswith(("Prof. ", "Dr. ")):
        title, name = name.split(None, 1)
    else:
        title = None
    user_id = "id-of-" + name.lower().replace(" ", "-")
    ext_id = f"{user_id}@lifescience-ri.eu"
    email = name.lower().replace(" ", ".") + "@home.org"
    role = "data_steward" if "steward" in name.lower() else None
    user: dict[str, Any] = {
        "_id": user_id,
        "status": "active",
        "name": name,
        "email": email,
        "title": title,
        "ext_id": ext_id,
        "registration_date": 1688472000,
    }
    # Add the user to the auth database. This is needed
    # because users are not registered as part of the test.
    fixtures.mongo.replace_document(
        fixtures.config.auth_db_name, fixtures.config.auth_users_collection, user
    )
    headers = fixtures.auth.generate_headers(
        id_=user_id, name=name, email=email, title=title, role=role
    )
    return LoginFixture(user, headers)


@then(parse('the response status code is "{code:d}"'))
def check_status_code(code: int, response: httpx.Response):
    assert response.status_code == code


# Global test bed state memory


@given("we start on a clean slate", target_fixture="state")
@async_step
async def reset_state(fixtures: JointFixture):
    await fixtures.s3.empty_buckets()  # empty object storage
    fixtures.kafka.delete_topics()  # empty event queues
    fixtures.mongo.empty_databases("tb")  # empty state database
    fixtures.mongo.empty_databases()  # empty service databases
    fixtures.dsk.reset_submission_dir()  # reset local submission registry
    fixtures.dsk.reset_unhappy_submission_dir()  # reset local unhappy submission registry
    empty_mail_server(fixtures.config)  # reset mail server


@given("we start on a clean unhappy submission registry", target_fixture="state")
@async_step
async def reset_unhappy_submission_dir(fixtures: JointFixture):
    fixtures.dsk.reset_unhappy_submission_dir()  # reset local unhappy submission registry


@given(parse('we have the state "{name}"'), target_fixture="state")
def assume_state_clause(name: str, mongo: MongoFixture):
    value = get_state(name, mongo)
    assert value, f'The expected state "{name}" has not yet been set.'
    return value


@then(parse('set the state to "{name}"'))
def set_state_clause(name: str, mongo: MongoFixture):
    set_state(name, True, mongo)


def get_state(state_name: str, mongo: MongoFixture) -> Any:
    state = mongo.find_document("tb", "state", {"_id": state_name})
    return (state or {}).get("value")


def set_state(state_name: str, value: Any, mongo: MongoFixture):
    mongo.replace_document("tb", "state", {"_id": state_name, "value": value})


def unset_state(state_regex: str, mongo: MongoFixture):
    mongo.remove_document("tb", "state", {"_id": {"$regex": state_regex}})


def empty_mail_server(config: Config):
    """Delete all e-mails from mail server"""
    httpx.delete(f"{config.mailhog_url}/api/v1/messages", timeout=TIMEOUT)


@then(parse('the expected hit count is "{count:d}"'))
def check_hit_count(count: int, response: httpx.Response):
    results = response.json()
    assert results["count"] == count


@then(parse('I receive "{item_count:d}" item'))
@then(parse('I receive "{item_count:d}" items'))
def check_received_item_count(response: httpx.Response, item_count):
    results = response.json()
    assert len(results["hits"]) == item_count


@given(
    parse('we have the "{config_state}" config with "{model_state}" metadata model'),
    target_fixture="metadata_config_path",
)
def metadata_config(config_state: str, model_state: str, fixtures: JointFixture):
    config_path_lookup = {
        "valid": fixtures.dsk.config.metadata_config_path,
        "unhappy": fixtures.dsk.config.unhappy_metadata_config_path,
    }
    metadata_config_path = config_path_lookup[config_state]

    if model_state == "unhappy":
        metadata_config_path = fixtures.dsk.get_updated_config(
            config_key="metadata_model_path", new_value="unhappy_metadata_model.yaml"
        )

    assert metadata_config_path.exists()
    return metadata_config_path
