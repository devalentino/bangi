from uuid import uuid4

from flask import make_response, redirect, request
from flask.views import MethodView

from src.container import container
from src.core.blueprint import Blueprint
from src.core.enums import FlowActionType
from src.core.services import ClientService, FlowService
from src.domains.services import DomainService
from src.tracker.schemas import (
    TrackClickRequestSchema,
    TrackLeadRequestSchema,
    TrackPostbackRequestSchema,
    TrackProcessRequestSchema,
)
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


@blueprint.route('/lead')
class TrackLead(MethodView):
    @blueprint.arguments(TrackLeadRequestSchema, location='query')
    @blueprint.response(201)
    def get(self, track_payload):
        track_click_service = container.get(TrackService)

        track_click_service.track_lead(track_payload.pop('clickId'), parameters=track_payload)

    @blueprint.arguments(TrackLeadRequestSchema)
    @blueprint.response(201)
    def post(self, track_payload):
        track_click_service = container.get(TrackService)

        track_click_service.track_lead(track_payload.pop('clickId'), parameters=track_payload)


@process_blueprint.route('/<int:campaignId>')
class Process(MethodView):
    @process_blueprint.arguments(TrackProcessRequestSchema, location='query')
    @process_blueprint.response(200)
    def get(self, process_payload, campaignId):
        track_click_service = container.get(TrackService)
        client_service = container.get(ClientService)
        flow_service = container.get(FlowService)
        domain_service = container.get(DomainService)

        click_id = process_payload.pop('clickId', None)
        if click_id is None:
            click_id = uuid4()

        track_click_service.track_click(click_id, campaign_id=campaignId, parameters=process_payload)

        client = client_service.client_info(
            request.user_agent.string, request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
        )
        domain = domain_service.get_by_campaign_id(campaignId)
        cookie_name = domain_service.cookie_name(domain.hostname, domain.purpose)
        cookie_value = request.cookies.get(cookie_name)
        action_type, subject, flow_id = flow_service.process_flows(campaignId, client, cookie_value)

        if action_type == FlowActionType.redirect:
            response = redirect(subject)
        elif action_type == FlowActionType.render:
            response = make_response(subject)
        else:
            track_click_service.track_discard(click_id, campaignId, client)
            return make_response('')

        if flow_id is not None:
            response.set_cookie(
                cookie_name,
                str(flow_id),
                httponly=True,
                path='/',
                max_age=60 * 60 * 24 * 365,
            )

        return response
