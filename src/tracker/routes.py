from flask import make_response, redirect, request
from flask.views import MethodView

from src.blueprint import Blueprint
from src.container import container
from src.core.enums import FlowActionType
from src.core.services import ClientService, FlowService
from src.tracker.schemas import TrackClickRequestSchema, TrackPostbackRequestSchema, TrackRedirectRequestSchema
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
            track_payload.pop('click_id'), track_payload.pop('campaign_id'), parameters=track_payload
        )


@blueprint.route('/postback')
class TrackPostback(MethodView):
    @blueprint.arguments(TrackPostbackRequestSchema, location='query')
    @blueprint.response(201)
    def get(self, track_payload):
        track_click_service = container.get(TrackService)

        track_click_service.track_postback(track_payload.pop('click_id'), parameters=track_payload)

    @blueprint.arguments(TrackPostbackRequestSchema)
    @blueprint.response(201)
    def post(self, track_payload):
        track_click_service = container.get(TrackService)

        track_click_service.track_postback(track_payload.pop('click_id'), parameters=track_payload)


@process_blueprint.route('/<int:campaign_id>')
class Process(MethodView):
    @process_blueprint.arguments(TrackRedirectRequestSchema, location='query')
    @process_blueprint.response(200)
    def get(self, redirect_payload, campaign_id):
        track_click_service = container.get(TrackService)
        client_service = container.get(ClientService)
        flow_service = container.get(FlowService)

        track_click_service.track_click(
            redirect_payload.pop('click_id'), campaign_id=campaign_id, parameters=redirect_payload
        )

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
