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

## creating building container
FROM python:3.10.9-slim-bullseye

# copy code
COPY . /app
WORKDIR /app

# install all requirements for running the tests
RUN python -m pip install --upgrade pip
RUN pip install --upgrade -r requirements.txt

# set environment
ENV PYTHONUNBUFFERED=1

# run the tests when the container starts
ENTRYPOINT ["pytest", "-v"]
