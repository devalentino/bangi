from flask.views import MethodView
from flask_smorest import Blueprint

blueprint = Blueprint('health', __name__, description='Health')


@blueprint.route('')
class Health(MethodView):

    @blueprint.response(200)
    def get(self):
        return {'healthy': True}
