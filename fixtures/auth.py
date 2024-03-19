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

"""Fixture for testing APIs that use an auth token."""

import json
from datetime import datetime
from pathlib import Path
from typing import NamedTuple, Optional

import pyotp
from ghga_service_commons.utils.jwt_helpers import sign_and_serialize_token
from ghga_service_commons.utils.utc_dates import DateTimeUTC
from httpx import Response
from jwcrypto import jwk
from pydantic import BaseModel, EmailStr
from pyparsing import Any
from pytest import fixture

from .config import Config
from .http_client import HttpClient

__all__ = ["auth_fixture"]

DEFAULT_VALID_SECONDS = 60 * 60  # 10 mins
DEFAULT_USER_STATUS = "active"


class Session(BaseModel):
    id: Optional[str] = None
    session_id: str
    csrf: str
    ext_id: str
    name: str
    email: EmailStr
    state: str
    timeout: int
    extends: int
    role: Optional[str] = None


class TokenGenerator:
    """Generator for auth tokens"""

    use_api_gateway: bool
    use_auth_adapter: bool
    key_file: Path
    auth_adapter_url: str
    op_url: str
    op_issuer: str
    titles = ("Dr.", "Prof.")
    user_domain = "home.org"

    def __init__(self, config: Config, http: HttpClient):
        self.use_api_gateway = config.use_api_gateway
        self.use_auth_adapter = config.use_auth_adapter
        self.key_file = config.auth_key_file
        self.op_url = config.op_url
        self.op_issuer = config.op_issuer
        self.auth_adapter_url = config.auth_adapter_url
        self.http = http

    @classmethod
    def split_title(cls, full_name: str) -> tuple[Optional[str], str]:
        """Split the full name into title and actual name."""
        if full_name.startswith(cls.titles):
            title, name = full_name.split(None, 1)
        else:
            title, name = None, full_name
        return title, name

    def get_user_id(self, full_name: str) -> str:
        """Get the plain identifier of the user without the domain."""
        name = self.split_title(full_name)[1]
        return "id-of-" + name.lower().replace(" ", "-")

    def get_sub(self, full_name: str) -> str:
        """Get the subject identifier of the user with the given full name."""
        user_id = self.get_user_id(full_name)
        op_domain = ".".join(
            self.op_issuer.split("://", 1)[-1].split("/", 1)[0].rsplit(".", 2)[-2:]
        )
        return f"{user_id}@{op_domain}"

    def get_email(self, full_name: str) -> str:
        """Get the email address of the user with the given full name."""
        name = self.split_title(full_name)[1]
        mail_id = name.lower().replace(" ", ".")
        return f"{mail_id}@{self.user_domain}"

    def internal_access_token_from_session(
        self, session_headers: dict, for_registration: bool = False
    ) -> str:
        """Get an internal from an external access token using the auth adapter."""
        url = self.auth_adapter_url + "/users"
        method = self.http.post if for_registration else self.http.get
        response = method(url, headers=session_headers)  # type: ignore
        status_code = response.status_code
        assert status_code == 200, status_code
        authorization = response.headers.get("Authorization")
        assert authorization and authorization.startswith("Bearer ")
        token = authorization.split(None, 1)[-1]
        assert token and token.count(".") == 2
        return token

    def internal_access_token_from_name(
        self,
        name: str,
        email: Optional[str] = None,
        title: Optional[str] = None,
        sub: Optional[str] = None,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        valid_seconds: Optional[int] = None,
    ) -> str:
        """Create an internal access token for the given name and email address."""
        email = self.get_email(name)
        role = "data_steward" if "steward" in name.lower() else None
        if not status:
            status = DEFAULT_USER_STATUS
        claims = {
            "name": name,
            "email": email,
            "title": title,
            "role": role,
            "status": status,
        }
        if user_id:
            claims["id"] = user_id
        if sub:
            claims["ext_id"] = sub
        if not valid_seconds:
            valid_seconds = DEFAULT_VALID_SECONDS
        return sign_and_serialize_token(claims, self.key, valid_seconds)

    def headers_for_session(self, session: Session) -> dict[str, str]:
        """Get proper headers for the given session."""
        return {
            "X-CSRF-Token": session.csrf,
            "Cookie": f"session={session.session_id}",
        }

    def session_from_response(self, response: Response) -> Session:
        """Get a session object from the response."""
        session_id = response.cookies.get("session")
        assert session_id
        session_header = response.headers.get("X-Session")
        assert session_header
        session_dict = json.loads(session_header)
        session = Session(session_id=session_id, **session_dict)
        return session

    def session(
        self,
        name: str,
        email: Optional[str] = None,
        title: Optional[str] = None,
        user_id: Optional[str] = None,
        valid_seconds: int = DEFAULT_VALID_SECONDS,
    ):
        """Login and return the session object

        Login to OIDC provider then with the external access token
        login to Auth Adapter in order to start a new session.

        Authenticate with two-factor authentication if necessary.
        """
        if title is None:
            title, name = self.split_title(name)
        sub = user_id if user_id else self.get_sub(name)
        external_token = self.oidc_login(
            name=name, email=email, sub=sub, valid_seconds=valid_seconds
        )
        auth_headers = {"Authorization": f"Bearer {external_token}"}
        response = self.auth_login(headers=auth_headers)
        session = self.session_from_response(response)
        return session

    def headers(
        self,
        session: Session,
    ):
        if self.use_api_gateway or self.use_auth_adapter:
            headers = self.headers_for_session(session=session)
            if not self.use_api_gateway:
                internal_token = self.internal_access_token_from_session(headers)
                headers = {"Authorization": f"Bearer {internal_token}"}
        else:
            # Is there any scenario where we don't have an Auth Adapter?
            internal_token = None
            headers = {"Authorization": f"Bearer {internal_token}"}
        return headers

    def oidc_login(
        self,
        name: str,
        email: Optional[str] = None,
        sub: Optional[str] = None,
        valid_seconds: Optional[int] = None,
    ):
        """Login with OpenID Connect."""
        if not valid_seconds:
            valid_seconds = DEFAULT_VALID_SECONDS
        login_info = {
            "name": name,
            "email": email,
            "valid_seconds": DEFAULT_VALID_SECONDS,
        }
        if sub:
            login_info["sub"] = sub
        url = self.op_url + "/login"
        response = self.http.post(url, json=login_info)
        status_code = response.status_code
        assert status_code == 201, status_code
        token = response.text
        assert token and token.count(".") == 2
        return token

    def auth_login(self, headers: dict[str, Any]):
        """Get or create session."""
        url = self.auth_adapter_url + "/rpc/login"
        response = self.http.post(url, json={}, headers=headers)
        status_code = response.status_code
        assert status_code == 204, status_code
        return response

    def get_totp_token(
        self, user_id: str, headers: dict[str, Any], force: bool = False
    ) -> str:
        """Request a valid TOTP token."""
        # TODO: Use existing TOTP token from state instead of a new one each time
        user_info = {"user_id": user_id, "force": force}
        url = self.auth_adapter_url + "/totp-token"
        response = self.http.post(url, json=user_info, headers=headers)
        status_code = response.status_code
        assert status_code == 200, status_code
        token = response.text
        return token

    def generate_totp(
        self, secret: str, when: Optional[datetime] = None, offset: int = 0
    ) -> str:
        """Generate a valid TOTP code for the given secret."""
        if not when:
            when = datetime.utcnow()
        return pyotp.TOTP(secret).at(when, offset)

    def verify_totp(self, user_id: str, totp: str, headers: dict[str, Any]) -> Response:
        """Verify the TOTP code."""
        user_info = {"user_id": user_id, "totp": totp}
        url = self.auth_adapter_url + "/verify-totp"
        return self.http.post(url, json=user_info, headers=headers)

    def auth_logout(
        self,
        session: Session,
    ):
        """Logout and remove session."""
        url = self.auth_adapter_url + "/rpc/logout"
        session_headers = self.headers_for_session(session)
        response = self.http.post(url, json={}, headers=session_headers)
        status_code = response.status_code
        assert status_code == 204, status_code

    def authenticate(self, session: Session, user_id: Optional[str] = None) -> Response:
        """Authenticate with two-factor authentication."""
        user_id = user_id if user_id else session.ext_id
        session_headers = self.headers_for_session(session)
        totp_token = self.get_totp_token(user_id=user_id, headers=session_headers)
        totp = self.generate_totp(totp_token)
        return self.verify_totp(user_id, totp, session_headers)

    @property
    def key(self) -> jwk.JWK:
        """Read the signing key from a local env file."""
        with open(self.key_file, encoding="ascii") as key_file:
            for line in key_file:
                if line.startswith("AUTH_SERVICE_AUTH_KEY="):
                    return jwk.JWK.from_json(line.split("=", 1)[1].rstrip().strip("'"))
        raise RuntimeError("Cannot read signing key for authentication")


@fixture(name="auth", scope="session")
def auth_fixture(config: Config, http: HttpClient) -> TokenGenerator:
    """Fixture that provides an auth token generator."""
    return TokenGenerator(config, http)
