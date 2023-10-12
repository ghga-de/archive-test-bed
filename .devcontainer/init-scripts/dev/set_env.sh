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
      ghga/auth-km-jobs:main generate-test-keys \
      --num-jwk=2 --num-c4gh=3 > $KEYS; then
    echo "Error: Testing keys could not be created."
    exit 1
  fi
fi
if ! grep -q "JWK_2_PRIV=" $KEYS ||
   ! grep -q "C4GH_3_PRIV=" $KEYS ||
   ! grep -q "TOKEN=" $KEYS; then
  echo "Error: Keys have not been properly created."
  echo "You may need to remove the keys.env file to recreate it."
  exit 1
fi

pk() {
  sed -n $1 $KEYS
}

pk "s/^JWK_1_PRIV=/AUTH_SERVICE_AUTH_KEY=/p" > auth.env
pk 's/^TOKEN=\(.*\)/SIMPLE_TOKEN="\1"/p' >> auth.env

pk "s/^C4GH_1_PUB=/WKVS_CRYPT4GH_PUBLIC_KEY=/p" > wkvs.env

pk 's/^TOKEN_HASH=\(.*\)/METLDATA_LOADER_TOKEN_HASHES=["\1"]/p' > metldata.env

pk 's/^TOKEN_HASH=\(.*\)/FIS_TOKEN_HASHES=["\1"]/p' > fis.env
pk "s/^C4GH_2_PRIV=/FIS_PRIVATE_KEY=/p" >> fis.env

pk "s/^C4GH_2_PUB=/TB_FIS_PUBKEY=/p" > tb.env
pk "s/^C4GH_3_PRIV=/TB_USER_PRIVATE_CRYPT4GH_KEY=/p" >> tb.env
pk "s/^C4GH_3_PUB=/TB_USER_PUBLIC_CRYPT4GH_KEY=/p" >> tb.env

pk "s/^C4GH_1_PRIV=/EKSS_SERVER_PRIVATE_KEY=/p" > ekss.env
pk "s/^C4GH_1_PUB=/EKSS_SERVER_PUBLIC_KEY=/p" >> ekss.env

pk "s/^JWK_1_PUB=/AUTH_SERVICE_AUTH_KEY=/p" > ums.env

pk "s/^JWK_1_PUB=/ARS_AUTH_KEY=/p" > ars.env

pk "s/^JWK_1_PUB=/WPS_AUTH_KEY=/p" > wps.env
pk "s/^JWK_2_PRIV=/WPS_WORK_PACKAGE_SIGNING_KEY=/p" >> wps.env

pk "s/^JWK_2_PUB=/DCS_AUTH_KEY=/p" > dcs.env

echo "Container envs have been created."
