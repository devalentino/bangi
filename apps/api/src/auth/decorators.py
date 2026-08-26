from flask import request
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth
from werkzeug.datastructures import Authorization

from src.auth.services import AuthenticationService


class QueryParameterTokenAuth(HTTPTokenAuth):
    """Bearer auth that also accepts the token via a `token` query parameter.

    Hosted MCP clients (Claude.ai, ChatGPT) can't yet send a custom Authorization header when
    connecting to a remote MCP server, so `/mcp` needs a header-equivalent fallback. The header
    takes precedence when both are present.
    """

    def get_auth(self):
        auth = super().get_auth()
        if auth is not None:
            return auth

        token = request.args.get('token')
        if not token:
            return None

        return Authorization(self.scheme, token=token)


auth = HTTPBasicAuth()
token_auth = QueryParameterTokenAuth(scheme='Bearer')


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
