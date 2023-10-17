#!/bin/bash

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

cd /workspace/example_data/metadata

# create directory for artifact models
rm -rf artifact_models
mkdir artifact_models

# create artifact infos and models
ghga-datasteward-kit metadata generate-artifact-models --config-path=metadata_config.yaml

# convert to yaml config, removing the json_schema properties
(
  echo "# metldata config auto-created with create_metldata_yaml.sh";
  echo "artifact_infos:";
  jq 'walk(if type == "object" and has("json_schema") then .json_schema = {} else . end)' \
    artifact_models/artifact_infos.json | sed 's/^/  /'
) > /workspace/.devcontainer/metldata.yaml

# remove directory with artifact models again
rm -rf artifact_models
