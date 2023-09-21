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
    StateStorage,
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
    state_fixture,
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
    if name.startswith(("Prof.", "Dr.")):
        title, name = name.split(".", 1)
        title += "."
        name = name.lstrip()
    else:
        title = None
    user_id = "id-of-" + name.lower().replace(" ", "-")
    email = name.lower().replace(" ", ".") + "@home.org"
    ext_id = f"{user_id}@ghga.de"
    user = fixtures.mongo.find_document(
        fixtures.config.ums_db_name,
        fixtures.config.ums_users_collection,
        {"ext_id": ext_id},
    )
    if not user:
        user = {
            "_id": user_id,
            "status": "active",
            "name": name,
            "email": email,
            "title": title,
            "ext_id": ext_id,
            "registration_date": 1688472000,
        }
        # Add the user to the auth database. This is needed
        # because users are not (yet) registered as part of the test.
        fixtures.mongo.replace_document(
            fixtures.config.ums_db_name, fixtures.config.ums_users_collection, user
        )
    headers = fixtures.auth.generate_headers(name=name, email=email, title=title)
    return LoginFixture(user, headers)


@then(parse('the response status code is "{code:d}"'))
def check_status_code(code: int, response: httpx.Response):
    assert response.status_code == code


# Global test bed state memory


def save_data_steward(fixtures: JointFixture) -> tuple[Any, Any]:
    data_steward_claim = fixtures.mongo.find_document(
        fixtures.config.ums_db_name,
        fixtures.config.ums_claims_collection,
        {"visa_value": "data_steward@ghga.de"},
    )
    data_steward = (
        fixtures.mongo.find_document(
            fixtures.config.ums_db_name,
            fixtures.config.ums_users_collection,
            {"_id": data_steward_claim["user_id"]},
        )
        if data_steward_claim
        else None
    )
    return data_steward, data_steward_claim


def restore_data_steward(state: tuple[Any, Any], fixtures: JointFixture) -> None:
    data_steward, data_steward_claim = state
    if data_steward:
        fixtures.mongo.replace_document(
            fixtures.config.ums_db_name,
            fixtures.config.ums_users_collection,
            data_steward,
        )
    if data_steward_claim:
        fixtures.mongo.replace_document(
            fixtures.config.ums_db_name,
            fixtures.config.ums_claims_collection,
            data_steward_claim,
        )


@given("we start on a clean slate")
@async_step
async def reset_state(fixtures: JointFixture):
    await fixtures.s3.empty_buckets()  # empty object storage
    fixtures.kafka.delete_topics()  # empty event queues
    fixtures.state.reset_state()  # empty state database
    saved_data_steward = save_data_steward(fixtures)
    fixtures.mongo.empty_databases()  # empty service databases
    restore_data_steward(saved_data_steward, fixtures)
    fixtures.dsk.reset_work_dir()  # reset local submission registry
    empty_mail_server(fixtures.config)  # reset mail server


@given(parse('we have the state "{name}"'))
def assume_state_clause(name: str, state: StateStorage):
    value = state.get_state(name)
    assert value, f'The expected state "{name}" has not yet been set.'
    return value


@then(parse('set the state to "{name}"'))
def set_state_clause(name: str, state: StateStorage):
    state.set_state(name, True)


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
