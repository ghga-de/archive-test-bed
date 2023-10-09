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

"""Step definitions for service health check using health endpoint"""

import httpx
from fixtures import Config
from fixtures.auth import TIMEOUT
from pytest_bdd import given, scenarios

scenarios("../features/01_health_check.feature")


@given("all the service APIs respond as expected")
def check_health_endpoints(config: Config):
    """Check 'health' endpoint of all service APIs"""
    health_endpoints = config.service_health_endpoints

    for endpoint in health_endpoints:
        response = httpx.get(endpoint, timeout=TIMEOUT)
        if config.use_api_gateway:
            # black-box testing: cannot reach service APIs directly
            assert (
                response.status_code == 404
            ), f"[black-box] Internal service is reachable: {endpoint}"
            return
        assert response.status_code == 200, f"Service is not reachable: {endpoint}"
