from flask.views import MethodView

from src.auth import auth
from src.blueprint import Blueprint

blueprint = Blueprint('auth', __name__, description='Auth')


@blueprint.route('/authenticate')
class Authenticate(MethodView):
    @blueprint.response(200)
    @auth.login_required
    def post(self):
        pass
