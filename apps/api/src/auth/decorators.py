from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth

from src.auth.services import AuthenticationService

auth = HTTPBasicAuth()
token_auth = HTTPTokenAuth(scheme='Bearer')


@auth.verify_password
def verify_password(username, password) -> None:
    from src.container import container

    authentication_service = container.get(AuthenticationService)
    if authentication_service.authenticate_basic_auth(username.strip(), password.strip()):
        return username
    return None


@token_auth.verify_token
def verify_token(token) -> None:
    from src.container import container

    return container.get(AuthenticationService).authenticate_pat_token(token) or None
