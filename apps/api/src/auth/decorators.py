from flask_httpauth import HTTPBasicAuth

from src.auth.services import AuthenticationService
from src.container import container

auth = HTTPBasicAuth()


@auth.verify_password
def verify_password(username, password) -> None:
    authentication_service = container.get(AuthenticationService)
    if authentication_service.authenticate(username, password):
        return username
    return None
