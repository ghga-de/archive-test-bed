#!/bin/sh

# Copyright 2023 Universität Tübingen, DKFZ and EMBL
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

cd .devcontainer

echo "Creating testing keys..."

KEYS=jwk.env

if ! docker run --rm ghga/auth-km-jobs:main generate-test-keys --num-jwk 2 > $KEYS ||
  ! grep -q "JWK_1_PUB=" $KEYS; then

  echo "Error: Testing keys could not be created."
  exit 1

fi

sed -n "s/^JWK_1_PUB=/AUTH_SERVICE_AUTH_KEY=/p" $KEYS > crs.env

sed -n "s/^JWK_1_PUB=/ARS_AUTH_KEY=/p" $KEYS > ars.env

sed -n "s/^JWK_1_PUB=/WPS_AUTH_KEY=/p" $KEYS > wps.env
sed -n "s/^JWK_2_PRIV=/WPS_WORK_PACKAGE_SIGNING_KEY=/p" $KEYS >> wps.env

sed -n "s/^JWK_1_PUB=/DCS_AUTH_KEY=/p" $KEYS > dcs.env

awk -F'=' '/TOKEN_HASH=/ { print "FIS_TOKEN_HASHES=[\""$2"\"]"}' $KEYS > fis.env
sed -n "s/^C4GH_PRIV=/FIS_PRIVATE_KEY=/p" $KEYS >> fis.env

sed -n "s/^C4GH_PUB=/GHGA_CONNECTOR_SERVER_PUBKEY=/p" $KEYS > tb.env

echo "Environments with testing keys have been created."
