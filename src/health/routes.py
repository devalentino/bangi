from flask.views import MethodView
from flask_smorest import Blueprint

from peewee import MySQLDatabase
from src.container import container

blueprint = Blueprint('health', __name__, description='Health')


@blueprint.route('')
class Health(MethodView):

    @blueprint.response(200)
    def get(self):
        db_connection = container.get(MySQLDatabase)

        if db_connection.is_connection_usable():
            return {'healthy': True}
        else:
            return {'healthy': False}, 503
