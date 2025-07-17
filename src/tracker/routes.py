from flask.views import MethodView
from flask_smorest import Blueprint

from src.container import container
from src.tracker.schemas import TrackClickRequestSchema
from src.tracker.services import TrackClickService

blueprint = Blueprint('tracker', __name__, description='Tracker')


@blueprint.route('/click')
class TrackClick(MethodView):
    @blueprint.arguments(TrackClickRequestSchema)
    @blueprint.response(201)
    def post(self, track_payload):
        track_click_service = container.get(TrackClickService)

        track_click_service.track(
            track_payload.pop('click_id'), track_payload.pop('campaign_id'), parameters=track_payload
        )
