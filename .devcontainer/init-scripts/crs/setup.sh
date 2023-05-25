#!/bin/bash

echo
echo Setup the Claims Repository Service
echo

pip install "hvac==1.1.0"

cat <<EOF > vault.py
import json
import os
import hvac

env = os.environ.get
url = env("VAULT_ADDR", "http://vault:8200")
token = env("VAULT_DEV_ROOT_TOKEN_ID", "dev-token")
vault = hvac.Client(
    url=url, namespace="vault", token=token,
    verify=False, timeout=10)

def out(setting, path):
    value = vault.secrets.kv.read_secret_version(
        path, raise_on_deleted_version=True)
    while "data" in value:
        value = value.pop("data")
    print(f"export AUTH_SERVICE_{setting.upper()}='{value}'")

out("auth_key", "auth/pub/int")
EOF

python vault.py >vault.env

source vault.env

auth-service
