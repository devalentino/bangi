from datetime import date

import humps
from flask.views import MethodView

from src.auth import auth
from src.blueprint import Blueprint
from src.container import container
from src.core.schemas import PaginationRequestSchema
from src.facebook_pacs.schemas import (
    AdCabinetListResponseSchema,
    AdCabinetRequestSchema,
    AdCabinetResponseSchema,
    BusinessPageListResponseSchema,
    BusinessPageRequestSchema,
    BusinessPageResponseSchema,
    BusinessPortfolioAccessUrlListResponseSchema,
    BusinessPortfolioAccessUrlRequestSchema,
    BusinessPortfolioAccessUrlResponseSchema,
    BusinessPortfolioListResponseSchema,
    BusinessPortfolioRequestSchema,
    BusinessPortfolioResponseSchema,
    CampaignListResponseSchema,
    CampaignRequestSchema,
    CampaignResponseSchema,
    ExecutorListResponseSchema,
    ExecutorRequestSchema,
    ExecutorResponseSchema,
)
from src.facebook_pacs.services import (
    AdCabinetService,
    BusinessPageService,
    BusinessPortfolioService,
    CampaignService,
    ExecutorService,
)

blueprint = Blueprint('facebook_pacs', __name__, description='Facebook PACs (Personal Ad Account)')


@blueprint.route('/executors')
class Executors(MethodView):
    @blueprint.arguments(PaginationRequestSchema, location='query')
    @blueprint.response(200, ExecutorListResponseSchema)
    @auth.login_required
    def get(self, parameters_payload):
        executor_service = container.get(ExecutorService)
        executors = executor_service.list(
            parameters_payload['page'],
            parameters_payload['pageSize'],
            humps.decamelize(parameters_payload['sortBy'].value),
            parameters_payload['sortOrder'],
        )
        count = executor_service.count()

        return {
            'content': [humps.camelize(e.to_dict()) for e in executors],
            'pagination': parameters_payload | {'total': count},
        }

    @blueprint.arguments(ExecutorRequestSchema)
    @blueprint.response(201, ExecutorResponseSchema)
    @auth.login_required
    def post(self, executor_payload):
        executor_service = container.get(ExecutorService)
        executor = executor_service.create(executor_payload['name'], executor_payload['isBanned'])
        return humps.camelize(executor.to_dict())


@blueprint.route('/executors/<int:executorId>')
class Executor(MethodView):
    @blueprint.response(200, ExecutorResponseSchema)
    @auth.login_required
    def get(self, executorId):
        executor_service = container.get(ExecutorService)
        executor = executor_service.get(executorId)
        return humps.camelize(executor.to_dict())

    @blueprint.arguments(ExecutorRequestSchema)
    @blueprint.response(200, ExecutorResponseSchema)
    @auth.login_required
    def patch(self, executor_payload, executorId):
        executor_service = container.get(ExecutorService)
        executor = executor_service.update(executorId, executor_payload.get('name'), executor_payload.get('isBanned'))
        return humps.camelize(executor.to_dict())


@blueprint.route('/business-portfolios')
class BusinessPosrfolios(MethodView):
    @blueprint.arguments(PaginationRequestSchema, location='query')
    @blueprint.response(200, BusinessPortfolioListResponseSchema)
    @auth.login_required
    def get(self, parameters_payload):
        business_portfolio_service = container.get(BusinessPortfolioService)
        business_portfolios = business_portfolio_service.list(
            parameters_payload['page'],
            parameters_payload['pageSize'],
            humps.decamelize(parameters_payload['sortBy'].value),
            parameters_payload['sortOrder'],
        )
        count = business_portfolio_service.count()

        return {
            'content': [humps.camelize(b.to_dict()) for b in business_portfolios],
            'pagination': parameters_payload | {'total': count},
        }

    @blueprint.arguments(BusinessPortfolioRequestSchema)
    @blueprint.response(201, BusinessPortfolioResponseSchema)
    @auth.login_required
    def post(self, business_portfolio_payload):
        business_portfolio_service = container.get(BusinessPortfolioService)
        business_portfolio = business_portfolio_service.create(
            business_portfolio_payload['name'], business_portfolio_payload['isBanned']
        )
        return humps.camelize(business_portfolio.to_dict())


@blueprint.route('/business-portfolios/<int:businessPortfolioId>')
class BusinessPortfolio(MethodView):
    @blueprint.response(200, BusinessPortfolioResponseSchema)
    @auth.login_required
    def get(self, businessPortfolioId):
        business_portfolio_service = container.get(BusinessPortfolioService)
        business_portfolio = business_portfolio_service.get(businessPortfolioId)
        return humps.camelize(business_portfolio.to_dict())

    @blueprint.arguments(BusinessPortfolioRequestSchema)
    @blueprint.response(200, BusinessPortfolioResponseSchema)
    @auth.login_required
    def patch(self, business_portfolio_payload, businessPortfolioId):
        business_portfolio_service = container.get(BusinessPortfolioService)
        business_portfolio = business_portfolio_service.update(
            businessPortfolioId, business_portfolio_payload.get('name'), business_portfolio_payload.get('isBanned')
        )
        return humps.camelize(business_portfolio.to_dict())


@blueprint.route('/business-portfolios/<int:businessPortfolioId>/executors/<int:executorId>')
class BusinessPortfolioAssignExecutor(MethodView):
    @blueprint.response(201, BusinessPortfolioResponseSchema)
    @auth.login_required
    def post(self, businessPortfolioId, executorId):
        business_portfolio_service = container.get(BusinessPortfolioService)
        business_portfolio = business_portfolio_service.bind_executor(businessPortfolioId, executorId)
        return humps.camelize(business_portfolio.to_dict())

    @blueprint.response(204, BusinessPortfolioResponseSchema)
    @auth.login_required
    def delete(self, businessPortfolioId, executorId):
        business_portfolio_service = container.get(BusinessPortfolioService)
        business_portfolio_service.unbind_executor(businessPortfolioId, executorId)


@blueprint.route('/business-portfolios/<int:businessPortfolioId>/access-urls')
class BusinessPortfolioAccessUrls(MethodView):
    @blueprint.arguments(PaginationRequestSchema, location='query')
    @blueprint.response(200, BusinessPortfolioAccessUrlListResponseSchema)
    @auth.login_required
    def get(self, parameters_payload, businessPortfolioId):
        business_portfolio_service = container.get(BusinessPortfolioService)
        access_urls = business_portfolio_service.list_access_urls(
            parameters_payload['page'],
            parameters_payload['pageSize'],
            humps.decamelize(parameters_payload['sortBy'].value),
            parameters_payload['sortOrder'],
            businessPortfolioId,
        )
        count = business_portfolio_service.count_access_urls()

        return {
            'content': [humps.camelize(a.to_dict()) for a in access_urls],
            'pagination': parameters_payload | {'total': count},
        }

    @blueprint.arguments(BusinessPortfolioAccessUrlRequestSchema)
    @blueprint.response(201, BusinessPortfolioAccessUrlResponseSchema)
    @auth.login_required
    def post(self, access_url_payload, businessPortfolioId):
        business_portfolio_service = container.get(BusinessPortfolioService)
        access_url = business_portfolio_service.create_access_url(
            businessPortfolioId, access_url_payload['url'], access_url_payload['expiresAt']
        )
        return humps.camelize(access_url.to_dict() | {'expiresAt': date.fromtimestamp(access_url.expires_at)})


@blueprint.route('/business-portfolios/<int:businessPortfolioId>/access-urls/<int:accessUrlId>')
class BusinessPortfolioAccessUrl(MethodView):
    @blueprint.response(204)
    @auth.login_required
    def delete(self, businessPortfolioId, accessUrlId):
        business_portfolio_service = container.get(BusinessPortfolioService)
        business_portfolio_service.delete_access_url(businessPortfolioId, accessUrlId)


@blueprint.route('/ad-cabinets')
class AdCabinets(MethodView):
    @blueprint.arguments(PaginationRequestSchema, location='query')
    @blueprint.response(200, AdCabinetListResponseSchema)
    @auth.login_required
    def get(self, parameters_payload):
        ad_cabinet_service = container.get(AdCabinetService)
        ad_cabinets = ad_cabinet_service.list(
            parameters_payload['page'],
            parameters_payload['pageSize'],
            humps.decamelize(parameters_payload['sortBy'].value),
            parameters_payload['sortOrder'],
        )
        count = ad_cabinet_service.count()

        return {
            'content': [humps.camelize(ac.to_dict()) for ac in ad_cabinets],
            'pagination': parameters_payload | {'total': count},
        }

    @blueprint.arguments(AdCabinetRequestSchema)
    @blueprint.response(201, AdCabinetResponseSchema)
    @auth.login_required
    def post(self, ad_cabinet_payload):
        ad_cabinet_service = container.get(AdCabinetService)
        ad_cabinet = ad_cabinet_service.create(ad_cabinet_payload['name'], ad_cabinet_payload['isBanned'])
        return humps.camelize(ad_cabinet.to_dict())


@blueprint.route('/ad-cabinets/<int:adCabinetId>')
class AdCabinet(MethodView):
    @blueprint.response(200, AdCabinetResponseSchema)
    @auth.login_required
    def get(self, adCabinetId):
        ad_cabinet_service = container.get(AdCabinetService)
        ad_cabinet = ad_cabinet_service.get(adCabinetId)
        return humps.camelize(ad_cabinet.to_dict())

    @blueprint.arguments(AdCabinetRequestSchema)
    @blueprint.response(200, AdCabinetResponseSchema)
    @auth.login_required
    def patch(self, ad_cabinet_payload, adCabinetId):
        ad_cabinet_service = container.get(AdCabinetService)
        ad_cabinet = ad_cabinet_service.update(
            adCabinetId, ad_cabinet_payload.get('name'), ad_cabinet_payload['isBanned']
        )
        return humps.camelize(ad_cabinet.to_dict())


@blueprint.route('/ad-cabinets/<int:adCabinetId>/business-portfolio/<int:businessPortfolioId>')
class AdCabinetAssignBusinessPortfolio(MethodView):
    @blueprint.response(201, AdCabinetResponseSchema)
    @auth.login_required
    def post(self, adCabinetId, businessPortfolioId):
        ad_cabinet_service = container.get(AdCabinetService)
        ad_cabinet = ad_cabinet_service.bind_business_portfolio(adCabinetId, businessPortfolioId)
        return humps.camelize(ad_cabinet.to_dict())

    @blueprint.response(204)
    @auth.login_required
    def delete(self, adCabinetId, businessPortfolioId):
        ad_cabinet_service = container.get(AdCabinetService)
        ad_cabinet_service.unbind_business_portfolio(adCabinetId, businessPortfolioId)


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
            'content': [humps.camelize(c.to_dict()) for c in campaigns],
            'pagination': parameters_payload | {'total': count},
        }

    @blueprint.arguments(CampaignRequestSchema)
    @blueprint.response(201)
    @auth.login_required
    def post(self, campaign_payload):
        campaign_service = container.get(CampaignService)
        campaign_service.create(
            campaign_payload['name'],
            campaign_payload['adCabinetId'],
            campaign_payload['executorId'],
            campaign_payload['businessPageId'],
        )


@blueprint.route('/campaigns/<int:campaignId>')
class Campaign(MethodView):
    @blueprint.response(200, CampaignResponseSchema)
    @auth.login_required
    def get(self, campaignId):
        campaign_service = container.get(CampaignService)
        campaign = campaign_service.get(campaignId)
        return humps.camelize(campaign.to_dict())

    @blueprint.arguments(CampaignRequestSchema)
    @blueprint.response(200)
    @auth.login_required
    def patch(self, campaign_payload, campaignId):
        campaign_service = container.get(CampaignService)
        campaign_service.update(
            campaignId,
            name=campaign_payload.get('name'),
            cost_value=campaign_payload.get('costValue'),
            currency=campaign_payload.get('currency'),
            ad_cabinet_id=campaign_payload.get('adCabinetId'),
            executor_id=campaign_payload.get('executorId'),
            business_page_id=campaign_payload.get('businessPageId'),
        )


@blueprint.route('/business-pages')
class BusinessPages(MethodView):
    @blueprint.arguments(PaginationRequestSchema, location='query')
    @blueprint.response(200, BusinessPageListResponseSchema)
    @auth.login_required
    def get(self, parameters_payload):
        business_page_service = container.get(BusinessPageService)
        business_pages = business_page_service.list(
            parameters_payload['page'],
            parameters_payload['pageSize'],
            humps.decamelize(parameters_payload['sortBy'].value),
            parameters_payload['sortOrder'],
        )
        count = business_page_service.count()

        return {
            'content': [humps.camelize(bp.to_dict()) for bp in business_pages],
            'pagination': parameters_payload | {'total': count},
        }

    @blueprint.arguments(BusinessPageRequestSchema)
    @blueprint.response(201, BusinessPageResponseSchema)
    @auth.login_required
    def post(self, business_page_payload):
        business_page_service = container.get(BusinessPageService)
        business_page = business_page_service.create(business_page_payload['name'], business_page_payload['isBanned'])
        return humps.camelize(business_page.to_dict())


@blueprint.route('/business-pages/<int:businessPageId>')
class BusinessPage(MethodView):
    @blueprint.response(200, BusinessPageResponseSchema)
    @auth.login_required
    def get(self, businessPageId):
        business_page_service = container.get(BusinessPageService)
        business_page = business_page_service.get(businessPageId)
        return humps.camelize(business_page.to_dict())

    @blueprint.arguments(BusinessPageRequestSchema)
    @blueprint.response(200, BusinessPageResponseSchema)
    @auth.login_required
    def patch(self, business_page_payload, businessPageId):
        business_page_service = container.get(BusinessPageService)
        business_page = business_page_service.update(
            businessPageId, business_page_payload.get('name'), business_page_payload.get('isBanned')
        )
        return humps.camelize(business_page.to_dict())
