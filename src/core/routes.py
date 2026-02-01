import humps
from flask import request
from flask.views import MethodView
from marshmallow import ValidationError

from src.auth import auth
from src.blueprint import Blueprint
from src.container import container
from src.core.enums import FlowActionType
from src.core.schemas import (
    CampaignCreateRequestSchema,
    CampaignListResponseSchema,
    CampaignResponseSchema,
    CampaignUpdateRequestSchema,
    FilterCampaignResponseSchema,
    FlowBulkOrderUpdateRequestSchema,
    FlowCreateRequestSchema,
    FlowListResponseSchema,
    FlowPaginationRequestSchema,
    FlowResponseSchema,
    FlowUpdateRequestSchema,
    PaginationRequestSchema,
)
from src.core.services import CampaignService, FlowService

blueprint = Blueprint('core', __name__, description='Core')


@blueprint.route('/campaigns')
class Campaigns(MethodView):
    @blueprint.arguments(PaginationRequestSchema, location='query')
    @blueprint.response(200, CampaignListResponseSchema)
    @auth.login_required
    def get(self, parameters_payload):
        campaign_service = container.get(CampaignService)
        campaigns = campaign_service.list(
            parameters_payload['page'],
            parameters_payload['pageSize'],
            humps.decamelize(parameters_payload['sortBy'].value),
            parameters_payload['sortOrder'],
        )
        count = campaign_service.count()

        return {
            'content': [
                humps.camelize(
                    c.to_dict()
                    | {'internal_process_url': f'{container.config.get("INTERNAL_PROCESS_BASE_URL")}/{c.id}'}
                )
                for c in campaigns
            ],
            'pagination': parameters_payload | {'total': count},
        }

    @blueprint.arguments(CampaignCreateRequestSchema)
    @blueprint.response(201)
    @auth.login_required
    def post(self, campaign_payload):
        campaign_service = container.get(CampaignService)
        campaign_service.create(
            campaign_payload['name'],
            campaign_payload['costModel'],
            campaign_payload['costValue'],
            campaign_payload['currency'],
            campaign_payload.get('statusMapper'),
        )


@blueprint.route('/campaigns/<int:campaign_id>')
class Campaign(MethodView):
    @blueprint.response(200, CampaignResponseSchema)
    @auth.login_required
    def get(self, campaign_id):
        campaign_service = container.get(CampaignService)
        campaign = campaign_service.get(campaign_id)
        return humps.camelize(
            campaign.to_dict()
            | {'internal_process_url': f'{container.config.get("INTERNAL_PROCESS_BASE_URL")}/{campaign.id}'}
        )

    @blueprint.arguments(CampaignUpdateRequestSchema)
    @blueprint.response(200)
    @auth.login_required
    def patch(self, campaign_payload, campaign_id):
        campaign_service = container.get(CampaignService)
        campaign_service.update(
            campaign_id,
            campaign_payload.get('name'),
            campaign_payload.get('costModel'),
            campaign_payload.get('costValue'),
            campaign_payload.get('currency'),
            campaign_payload.get('statusMapper'),
        )


@blueprint.route('/filters/campaigns')
class FilterCampaigns(MethodView):
    @blueprint.response(200, FilterCampaignResponseSchema(many=True))
    @auth.login_required
    def get(self):
        campaign_service = container.get(CampaignService)
        campaigns = campaign_service.all()
        return [c.to_dict() for c in campaigns]


@blueprint.route('/campaigns/<int:campaign_id>/flows')
class CampaignFlows(MethodView):
    @blueprint.arguments(FlowPaginationRequestSchema, location='query')
    @blueprint.response(200, FlowListResponseSchema)
    @auth.login_required
    def get(self, parameters_payload, campaign_id):
        flow_service = container.get(FlowService)
        flows = flow_service.list(
            parameters_payload['page'],
            parameters_payload['pageSize'],
            humps.decamelize(parameters_payload['sortBy'].value),
            parameters_payload['sortOrder'],
            campaign_id=campaign_id,
        )
        count = flow_service.count(campaign_id=campaign_id)

        return {
            'content': [
                humps.camelize(
                    f.to_dict()
                    | {
                        'campaign_id': f.campaign.id,
                        'campaign_name': f.campaign.name,
                        'landing_path': (
                            f'{container.config.get("LANDING_PAGES_BASE_PATH")}/{f.id}'
                            if f.action_type == FlowActionType.render
                            else None
                        ),
                    }
                )
                for f in flows
            ],
            'pagination': parameters_payload | {'total': count},
        }

    @blueprint.arguments(FlowCreateRequestSchema, location='form')
    @blueprint.response(201)
    @auth.login_required
    def post(self, flow_payload, campaign_id):
        landing_archive = request.files.get('landingArchive')

        try:
            FlowCreateRequestSchema.validate_render_action_type(flow_payload, landing_archive)
        except ValidationError as e:
            return {
                'code': 422,
                'errors': {'form': {'landingArchive': e.messages}},
                'status': 'Unprocessable Entity',
            }, 422

        flow_service = container.get(FlowService)
        flow_service.create(
            flow_payload['name'],
            campaign_id,
            flow_payload['rule'],
            flow_payload['actionType'],
            flow_payload.get('redirectUrl'),
            flow_payload.get('isEnabled', True),
            landing_archive,
        )


@blueprint.route('/campaigns/<int:campaign_id>/flows/<int:flow_id>')
class Flow(MethodView):
    @blueprint.response(200, FlowResponseSchema)
    @auth.login_required
    def get(self, campaign_id, flow_id):
        flow_service = container.get(FlowService)
        flow = flow_service.get(flow_id, campaign_id)
        return humps.camelize(
            flow.to_dict()
            | {
                'campaign_id': flow.campaign.id,
                'campaign_name': flow.campaign.name,
                'landing_path': (
                    f'{container.config.get("LANDING_PAGES_BASE_PATH")}/{flow.id}'
                    if flow.action_type == FlowActionType.render
                    else None
                ),
            }
        )

    @blueprint.arguments(FlowUpdateRequestSchema, location='form')
    @blueprint.response(200)
    @auth.login_required
    def patch(self, flow_payload, campaign_id, flow_id):
        landing_archive = request.files.get('landingArchive')

        try:
            FlowUpdateRequestSchema.validate_render_action_type(flow_payload, landing_archive)
        except ValidationError as e:
            return {
                'code': 422,
                'errors': {'form': {'landingArchive': e.messages}},
                'status': 'Unprocessable Entity',
            }, 422

        flow_service = container.get(FlowService)
        flow_service.update(
            flow_id,
            campaign_id,
            flow_payload.get('name'),
            flow_payload.get('rule'),
            flow_payload.get('actionType'),
            flow_payload.get('redirectUrl'),
            flow_payload.get('isEnabled'),
            landing_archive,
        )

    @blueprint.response(204)
    @auth.login_required
    def delete(self, campaign_id, flow_id):
        flow_service = container.get(FlowService)
        flow_service.delete(flow_id, campaign_id)


@blueprint.route('/campaigns/<int:campaign_id>/flows/order')
class FlowOrder(MethodView):
    @blueprint.arguments(FlowBulkOrderUpdateRequestSchema, location='json')
    @blueprint.response(200)
    @auth.login_required
    def patch(self, payload, campaign_id):
        flow_service = container.get(FlowService)
        flow_service.bulk_update_order(campaign_id, payload['order'])
