from typing import Annotated

from wireup import Inject, injectable


@injectable(lifetime='singleton')
class AuthenticationService:
    def __init__(
        self,
        basic_authentication_username: Annotated[str, Inject(config='BASIC_AUTHENTICATION_USERNAME')],
        basic_authentication_password: Annotated[str, Inject(config='BASIC_AUTHENTICATION_PASSWORD')],
    ):
        self.basic_authentication_username = basic_authentication_username
        self.basic_authentication_password = basic_authentication_password

    def authenticate(self, username: str, password: str) -> bool:
        if username == self.basic_authentication_username and password == self.basic_authentication_password:
            return True

        return False
