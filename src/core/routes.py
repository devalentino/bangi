import humps
from flask.views import MethodView

from src.auth import auth
from src.blueprint import Blueprint
from src.container import container
from src.core.schemas import (
    CampaignCreateRequestSchema,
    CampaignListResponseSchema,
    CampaignResponseSchema,
    CampaignUpdateRequestSchema,
    FilterCampaignResponseSchema,
    PaginationRequestSchema,
)
from src.core.services import CampaignService

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
            parameters_payload['page_size'],
            parameters_payload['sort_by'],
            parameters_payload['sort_order'],
        )
        count = campaign_service.count()

        return {
            'content': [humps.camelize(c.to_dict()) for c in campaigns],
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
        )


@blueprint.route('/campaigns/<int:campaign_id>')
class Campaign(MethodView):
    @blueprint.response(200, CampaignResponseSchema)
    @auth.login_required
    def get(self, campaign_id):
        campaign_service = container.get(CampaignService)
        campaign = campaign_service.get(campaign_id)
        return humps.camelize(campaign.to_dict())

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
        )


@blueprint.route('/filters/campaigns')
class FilterCampaigns(MethodView):
    @blueprint.response(200, FilterCampaignResponseSchema(many=True))
    @auth.login_required
    def get(self):
        campaign_service = container.get(CampaignService)
        campaigns = campaign_service.all()
        return [c.to_dict() for c in campaigns]
