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

echo "Creating container envs..."

KEYS=keys.env

if [ -s $KEYS ]; then
  echo "Reusing existing testing keys..."
else
  echo "Creating new testing keys..."
  if ! docker run --rm \
      ghga/auth-km-jobs:main generate-test-keys --num-jwk=2 --num-c4gh=2 \
      > $KEYS; then
    echo "Error: Testing keys could not be created."
    exit 1
  fi
fi
if ! grep -q "JWK_1_PRIV=" $KEYS ||
   ! grep -q "C4GH_1_PRIV=" $KEYS ||
   ! grep -q "TOKEN=" $KEYS; then
  echo "Error: Keys have not been properly created."
  echo "You may need to remove the keys.env file to recreate it."
  exit 1
fi

sed -n "s/^JWK_1_PRIV=/AUTH_KEY=/p" $KEYS > auth.env
sed -n 's/^TOKEN=\(.*\)/SIMPLE_TOKEN="\1"/p' $KEYS >> auth.env

sed -n "s/^C4GH_1_PUB=/WKVS_CRYPT4GH_PUBLIC_KEY=/p" $KEYS > wkvs.env

sed -n 's/^TOKEN=\(.*\)/FIS_TOKEN="\1"/p' $KEYS > fis.env
sed -n 's/^TOKEN_HASH=\(.*\)/FIS_TOKEN_HASHES=["\1"]/p' $KEYS >> fis.env
sed -n "s/^C4GH_2_PRIV=/FIS_PRIVATE_KEY=/p" $KEYS >> fis.env

sed -n "s/^C4GH_2_PUB=/TB_FILE_INGEST_PUBKEY=/p" $KEYS > tb.env

sed -n "s/^C4GH_1_PRIV=/EKSS_SERVER_PRIVATE_KEY=/p" $KEYS > ekss.env
sed -n "s/^C4GH_1_PUB=/EKSS_SERVER_PUBLIC_KEY=/p" $KEYS >> ekss.env

sed -n "s/^JWK_1_PUB=/AUTH_SERVICE_AUTH_KEY=/p" $KEYS > crs.env

sed -n "s/^JWK_1_PUB=/ARS_AUTH_KEY=/p" $KEYS > ars.env

sed -n "s/^JWK_1_PUB=/WPS_AUTH_KEY=/p" $KEYS > wps.env
sed -n "s/^JWK_2_PRIV=/WPS_WORK_PACKAGE_SIGNING_KEY=/p" $KEYS >> wps.env

sed -n "s/^JWK_1_PUB=/DCS_AUTH_KEY=/p" $KEYS > dcs.env

echo "Container envs have been created."
