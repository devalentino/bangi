from flask import request
from flask.views import MethodView

from src.auth import token_auth
from src.core.blueprint import Blueprint
from src.mcp import protocol
from src.mcp.schemas import JsonRpcRequestSchema

blueprint = Blueprint('mcp', __name__, description='MCP')

_KNOWN_TOOL_NAMES = {tool['name'] for tool in protocol.TOOL_DEFINITIONS}


@blueprint.route('')
class Mcp(MethodView):
    @blueprint.arguments(JsonRpcRequestSchema)
    @blueprint.response(200)
    @token_auth.login_required
    def post(self, body):
        try:
            protocol.validate_headers(request.headers, body)
        except protocol.ProtocolError as error:
            return protocol.error_response(error)

        if body['method'] == 'server/discover':
            return protocol.discover_response()
        if body['method'] == 'tools/list':
            return protocol.list_tools_response()
        if body['method'] == 'tools/call':
            return call_tool(body['params'])

        return protocol.error_response(protocol.ProtocolError(-32601, 'MethodNotFound', 404))


def call_tool(params):
    name = params.get('name')
    arguments = params.get('arguments', {})

    if name not in _KNOWN_TOOL_NAMES:
        return protocol.error_response(protocol.ProtocolError(-32602, 'InvalidParams', 400))

    return {'name': name, 'arguments': arguments}
