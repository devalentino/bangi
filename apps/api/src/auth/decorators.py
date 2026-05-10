from flask_httpauth import HTTPBasicAuth

from src.auth.services import AuthenticationService

auth = HTTPBasicAuth()


@auth.verify_password
def verify_password(username, password) -> None:
    from src.container import container

    authentication_service = container.get(AuthenticationService)
    if authentication_service.authenticate(username.strip(), password.strip()):
        return username
    return None
