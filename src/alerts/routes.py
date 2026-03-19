from flask.views import MethodView

from src.alerts.schemas import AlertListResponseSchema
from src.alerts.services import AlertService
from src.auth import auth
from src.blueprint import Blueprint
from src.container import container

blueprint = Blueprint('alerts', __name__, description='Alerts')


@blueprint.route('')
class Alerts(MethodView):
    @blueprint.response(200, AlertListResponseSchema)
    @auth.login_required
    def get(self):
        alert_service = container.get(AlertService)
        return {'content': alert_service.serialize(alert_service.collect())}
