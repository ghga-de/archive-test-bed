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

"""Step definition for service health check using health endpoint"""

from pytest_bdd import given, scenarios

from .conftest import JointFixture

scenarios("../features/01_health_check.feature")


def check_api_is_healthy(api: str, fixtures: JointFixture):
    """Check that service API is healthy or not reachable if internal."""
    config = fixtures.config
    is_internal = config.use_api_gateway and api in config.internal_apis
    health_endpoint = getattr(config, f"{api}_url").rstrip("/")
    if api == "mail":
        health_endpoint += "/api/v2/messages"
    else:
        health_endpoint += "/health"
    response = fixtures.http.get(health_endpoint)
    status_code = response.status_code
    expected_status = 404 if is_internal else 200
    if status_code == 200 and response.text.startswith("<!doctype html>"):
        # count response from frontend as "not found"
        status_code = 404
    msg = None
    if status_code != expected_status:
        msg = f"status should be {expected_status}, but is {status_code}"
    elif not is_internal:
        ret = response.json()
        if not isinstance(ret, dict):
            msg = "does not return JSON object"
        if api == "mail":
            ok = "total" in ret
        else:
            ok = ret.get("status") == "OK"
        if not ok:
            msg = f"unexpected response: {ret}"
    assert not msg, f"Health check at endpoint {health_endpoint}: {msg}"


@given("all the service APIs respond as expected")
def check_service_health(fixtures: JointFixture):
    """Check health of all service APIs depending on the test mode."""
    config = fixtures.config
    for api in config.external_apis + config.internal_apis:
        check_api_is_healthy(api, fixtures)
