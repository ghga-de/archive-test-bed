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


def is_frontend(text: str) -> bool:
    """Check if the given response text is produced by the frontend."""
    return (
        text.startswith("<!doctype html>")
        and "<title>GHGA" in text
        and "<script" in text
    )


def check_api_health(
    api: str,
    expected_status_code: int,
    fixtures: JointFixture,
) -> None:
    """Check service API returns expected status code"""
    health_endpoint = getattr(fixtures.config, f"{api}_url")
    if api != "mail":  # mailhog has no /health endpoint
        health_endpoint = health_endpoint.rstrip("/") + "/health"
    response = fixtures.http.get(health_endpoint)
    status_code = response.status_code
    if status_code == 200 and is_frontend(response.text):
        status_code = 404  # can only reach the frontend, treat it as 404
    assert status_code == expected_status_code, (
        f"Expected status {expected_status_code}"
        f" instead of {status_code} at {health_endpoint}"
    )


@given("all the service APIs respond as expected")
def check_service_health(fixtures: JointFixture):
    """Check 'health' endpoint of all service APIs"""
    config = fixtures.config
    if config.use_api_gateway:
        # black-box testing: external APIs are accessible, internal APIs are not
        for ext_api in config.external_apis:
            check_api_health(ext_api, 200, fixtures)
        for int_api in config.internal_apis:
            check_api_health(int_api, 404, fixtures)
    else:
        # white-box testing: all of the APIs are accessible
        all_apis = config.external_apis + config.internal_apis
        for api in all_apis:
            check_api_health(api, 200, fixtures)
