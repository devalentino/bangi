import humps
from flask.views import MethodView

from src.auth import auth
from src.auth.schemas import PatTokenCreateRequestSchema, PatTokenCreateResponseSchema, PatTokenListResponseSchema
from src.auth.services import PatTokenService
from src.container import container
from src.core.blueprint import Blueprint

blueprint = Blueprint('auth', __name__, description='Auth')


@blueprint.route('/authenticate')
class Authenticate(MethodView):
    @blueprint.response(200)
    @auth.login_required
    def post(self):
        pass


@blueprint.route('/tokens')
class PatTokens(MethodView):
    @blueprint.response(200, PatTokenListResponseSchema)
    @auth.login_required
    def get(self):
        pat_token_service = container.get(PatTokenService)
        return {
            'content': [
                humps.camelize(
                    {
                        'id': token.id,
                        'name': token.name,
                        'created_at': int(token.created_at.timestamp()),
                        'revoked_at': None if token.revoked_at is None else int(token.revoked_at.timestamp()),
                        'token_prefix': token.token_prefix,
                        'token_suffix': token.token_suffix,
                    }
                )
                for token in pat_token_service.list()
            ]
        }

    @blueprint.arguments(PatTokenCreateRequestSchema)
    @blueprint.response(201, PatTokenCreateResponseSchema)
    @auth.login_required
    def post(self, payload):
        pat_token_service = container.get(PatTokenService)
        token = pat_token_service.generate(payload['name'])
        return {'token': token, 'name': payload['name']}


@blueprint.route('/tokens/<int:tokenId>')
class PatTokenItem(MethodView):
    @blueprint.response(204)
    @auth.login_required
    def delete(self, tokenId):
        pat_token_service = container.get(PatTokenService)
        pat_token_service.revoke(tokenId)
