from uuid import uuid4

from flask import make_response, redirect, request
from flask.views import MethodView

from src.blueprint import Blueprint
from src.container import container
from src.core.enums import FlowActionType
from src.core.services import ClientService, FlowService
from src.tracker.schemas import TrackClickRequestSchema, TrackPostbackRequestSchema, TrackProcessRequestSchema
from src.tracker.services import TrackService

blueprint = Blueprint('tracker', __name__, description='Tracker')
process_blueprint = Blueprint('process', __name__, description='Tracker Process')


@blueprint.route('/click')
class TrackClick(MethodView):
    @blueprint.arguments(TrackClickRequestSchema)
    @blueprint.response(201)
    def post(self, track_payload):
        track_click_service = container.get(TrackService)

        track_click_service.track_click(
            track_payload.pop('clickId'), track_payload.pop('campaignId'), parameters=track_payload
        )


@blueprint.route('/postback')
class TrackPostback(MethodView):
    @blueprint.arguments(TrackPostbackRequestSchema, location='query')
    @blueprint.response(201)
    def get(self, track_payload):
        track_click_service = container.get(TrackService)

        track_click_service.track_postback(track_payload.pop('clickId'), parameters=track_payload)

    @blueprint.arguments(TrackPostbackRequestSchema)
    @blueprint.response(201)
    def post(self, track_payload):
        track_click_service = container.get(TrackService)

        track_click_service.track_postback(track_payload.pop('clickId'), parameters=track_payload)


@process_blueprint.route('/<int:campaign_id>')
class Process(MethodView):
    @process_blueprint.arguments(TrackProcessRequestSchema, location='query')
    @process_blueprint.response(200)
    def get(self, process_payload, campaign_id):
        track_click_service = container.get(TrackService)
        client_service = container.get(ClientService)
        flow_service = container.get(FlowService)

        click_id = process_payload.pop('clickId', None)
        if click_id is None:
            click_id = str(uuid4())

        track_click_service.track_click(click_id, campaign_id=campaign_id, parameters=process_payload)

        action_type, subject = flow_service.process_flows(
            campaign_id,
            client_service.client_info(
                request.user_agent.string, request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
            ),
        )

        if action_type == FlowActionType.redirect:
            return redirect(subject)
        elif action_type == FlowActionType.render:
            return make_response(subject)
        else:
            return make_response('')
