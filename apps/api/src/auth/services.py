import hashlib
import secrets
from typing import Annotated

from wireup import Inject, injectable

from src.auth.entities import PatToken
from src.core.utils import utcnow


@injectable
class BasicAuthenticationService:
    def __init__(
        self,
        basic_authentication_username: Annotated[str, Inject(config='BASIC_AUTHENTICATION_USERNAME')],
        basic_authentication_password: Annotated[str, Inject(config='BASIC_AUTHENTICATION_PASSWORD')],
    ):
        self.basic_authentication_username = basic_authentication_username
        self.basic_authentication_password = basic_authentication_password

    def authenticate(self, username: str, password: str) -> bool:
        return username == self.basic_authentication_username and password == self.basic_authentication_password


@injectable
class PatTokenService:
    def generate(self, name: str) -> str:
        token = secrets.token_urlsafe(32)
        PatToken.create(name=name, token_hash=self._hash(token), token_prefix=token[:8], token_suffix=token[-4:])
        return token

    def verify(self, token: str) -> bool:
        return PatToken.select().where(PatToken.token_hash == self._hash(token), PatToken.revoked_at.is_null()).exists()

    def revoke(self, token_id: int) -> None:
        PatToken.update(revoked_at=utcnow()).where(PatToken.id == token_id).execute()

    def list(self):
        return list(PatToken.select())

    @staticmethod
    def _hash(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()


@injectable
class AuthenticationService:
    def __init__(self, basic: BasicAuthenticationService, pat_token_service: PatTokenService):
        self._basic = basic
        self._pat_token_service = pat_token_service

    def authenticate_basic_auth(self, username: str, password: str) -> bool:
        return self._basic.authenticate(username, password)

    def authenticate_pat_token(self, token: str) -> bool:
        return self._pat_token_service.verify(token)
