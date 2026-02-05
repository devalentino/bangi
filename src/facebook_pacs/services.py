from datetime import datetime, time

from wireup import service

from peewee import IntegrityError, fn
from src.core.enums import SortOrder
from src.core.exceptions import DoesNotExistError
from src.core.services import CampaignService as CoreCampaignService
from src.facebook_pacs import exceptions
from src.facebook_pacs.entities import (
    AdCabinet,
    BusinessPage,
    BusinessPortfolio,
    BusinessPortfolioAccessUrl,
    Campaign,
    Executor,
)
from src.facebook_pacs.exceptions import ExecutorIsAlreadyBindError


@service
class ExecutorService:
    def get(self, id):
        try:
            return Executor.get_by_id(id)
        except Executor.DoesNotExist as exc:
            raise DoesNotExistError() from exc

    def list(self, page, page_size, sort_by, sort_order, partial_name=None):
        order_by = getattr(Executor, sort_by)
        if sort_order == SortOrder.desc:
            order_by = order_by.desc()

        query = Executor.select()
        if partial_name:
            query = query.where(fn.LOWER(Executor.name).contains(partial_name.lower()))

        return [e for e in query.order_by(order_by).limit(page_size).offset(page - 1)]

    def create(self, name, is_banned):
        executor = Executor(name=name, is_banned=is_banned)
        executor.save()
        return executor

    def update(self, executor_id, name=None, is_banned=None):
        executor = self.get(executor_id)

        if name:
            executor.name = name

        if is_banned is not None:
            executor.is_banned = is_banned

        executor.save()
        return executor

    def count(self, partial_name=None):
        query = Executor.select(fn.count(Executor.id))
        if partial_name:
            query = query.where(fn.LOWER(Executor.name).contains(partial_name.lower()))
        return query.scalar()


@service
class BusinessPortfolioService:
    def __init__(self, executor_service: ExecutorService):
        self.executor_service = executor_service

    def get(self, id):
        try:
            return BusinessPortfolio.get_by_id(id)
        except BusinessPortfolio.DoesNotExist as exc:
            raise DoesNotExistError() from exc

    def list(self, page, page_size, sort_by, sort_order, partial_name=None):
        order_by = getattr(BusinessPortfolio, sort_by)
        if sort_order == SortOrder.desc:
            order_by = order_by.desc()

        query = BusinessPortfolio.select()
        if partial_name:
            query = query.where(fn.LOWER(BusinessPortfolio.name).contains(partial_name.lower()))

        return [bm for bm in query.order_by(order_by).limit(page_size).offset(page - 1)]

    def create(self, name, is_banned):
        business_portfolio = BusinessPortfolio(name=name, is_banned=is_banned)
        business_portfolio.save()
        return business_portfolio

    def update(self, business_portfolio_id, name=None, is_banned=None):
        business_portfolio = self.get(business_portfolio_id)

        if name:
            business_portfolio.name = name

        if is_banned is not None:
            business_portfolio.is_banned = is_banned

        business_portfolio.save()
        return business_portfolio

    def count(self, partial_name=None):
        query = BusinessPortfolio.select(fn.count(BusinessPortfolio.id))
        if partial_name:
            query = query.where(fn.LOWER(BusinessPortfolio.name).contains(partial_name.lower()))
        return query.scalar()

    def bind_executor(self, business_portfolio_id, executor_id):
        executor = self.executor_service.get(executor_id)
        business_portfolio = self.get(business_portfolio_id)

        try:
            business_portfolio.executors.add(executor)
        except IntegrityError as exp:
            raise ExecutorIsAlreadyBindError from exp

        business_portfolio.save()

        return business_portfolio

    def unbind_executor(self, business_portfolio_id, executor_id):
        executor = self.executor_service.get(executor_id)
        business_portfolio = self.get(business_portfolio_id)

        business_portfolio.executors.remove(executor)
        business_portfolio.save()

        return business_portfolio

    def create_access_url(self, business_portfolio_id, url, expires_at):
        business_portfolio = self.get(business_portfolio_id)
        expires_at_timestamp = datetime.combine(expires_at, time.min).timestamp()
        access_url = BusinessPortfolioAccessUrl(
            business_portfolio=business_portfolio, url=url, expires_at=expires_at_timestamp
        )
        access_url.save()
        return access_url

    def list_access_urls(self, page, page_size, sort_by, sort_order, business_portfolio_id):
        order_by = getattr(BusinessPortfolioAccessUrl, sort_by)
        if sort_order == SortOrder.desc:
            order_by = order_by.desc()

        return [
            a
            for a in BusinessPortfolioAccessUrl.select()
            .where(BusinessPortfolioAccessUrl.business_portfolio == business_portfolio_id)
            .order_by(order_by)
            .limit(page_size)
            .offset(page - 1)
        ]

    def count_access_urls(self):
        return BusinessPortfolioAccessUrl.select(fn.count(BusinessPortfolioAccessUrl.id)).scalar()

    def delete_access_url(self, business_portfolio_id, access_url_id):
        query = BusinessPortfolioAccessUrl.delete().where(
            (BusinessPortfolioAccessUrl.id == access_url_id)
            & (BusinessPortfolioAccessUrl.business_portfolio == business_portfolio_id)
        )
        query.execute()


@service
class AdCabinetService:
    def __init__(self, business_portfolio_service: BusinessPortfolioService):
        self.business_portfolio_service = business_portfolio_service

    def get(self, id):
        try:
            return AdCabinet.get_by_id(id)
        except AdCabinet.DoesNotExist as exc:
            raise DoesNotExistError() from exc

    def list(self, page, page_size, sort_by, sort_order, partial_name=None):
        order_by = getattr(AdCabinet, sort_by)
        if sort_order == SortOrder.desc:
            order_by = order_by.desc()

        query = AdCabinet.select()
        if partial_name:
            query = query.where(fn.LOWER(AdCabinet.name).contains(partial_name.lower()))

        return [ac for ac in query.order_by(order_by).limit(page_size).offset(page - 1)]

    def create(self, name, is_banned):
        ad_cabinet = AdCabinet(name=name, is_banned=is_banned)
        ad_cabinet.save()
        return ad_cabinet

    def update(self, ad_cabinet_id, name=None, is_banned=None):
        ad_cabinet = self.get(ad_cabinet_id)

        if name:
            ad_cabinet.name = name

        if is_banned is not None:
            ad_cabinet.is_banned = is_banned

        ad_cabinet.save()
        return ad_cabinet

    def count(self, partial_name=None):
        query = AdCabinet.select(fn.count(AdCabinet.id))
        if partial_name:
            query = query.where(fn.LOWER(AdCabinet.name).contains(partial_name.lower()))
        return query.scalar()

    def bind_business_portfolio(self, ad_cabinet_id, business_portfolio_id):
        business_portfolio = self.business_portfolio_service.get(business_portfolio_id)
        ad_cabinet = self.get(ad_cabinet_id)

        ad_cabinet.business_portfolio_id = business_portfolio.id
        ad_cabinet.save()

        return ad_cabinet

    def unbind_business_portfolio(self, ad_cabinet_id, business_portfolio_id):
        ad_cabinet = self.get(ad_cabinet_id)
        if ad_cabinet.business_portfolio_id != business_portfolio_id:
            raise exceptions.BadBusinessPortfolioError()

        ad_cabinet.business_portfolio_id = None
        ad_cabinet.save()


@service
class BusinessPageService:
    def get(self, id):
        try:
            return BusinessPage.get_by_id(id)
        except BusinessPage.DoesNotExist as exc:
            raise DoesNotExistError() from exc

    def list(self, page, page_size, sort_by, sort_order, partial_name=None):
        order_by = getattr(BusinessPage, sort_by)
        if sort_order == SortOrder.desc:
            order_by = order_by.desc()

        query = BusinessPage.select()
        if partial_name:
            query = query.where(fn.LOWER(BusinessPage.name).contains(partial_name.lower()))

        return [bp for bp in query.order_by(order_by).limit(page_size).offset(page - 1)]

    def create(self, name, is_banned):
        business_page = BusinessPage(name=name, is_banned=is_banned)
        business_page.save()
        return business_page

    def update(self, business_page_id, name=None, is_banned=None):
        business_page = self.get(business_page_id)

        if name:
            business_page.name = name

        if is_banned is not None:
            business_page.is_banned = is_banned

        business_page.save()
        return business_page

    def count(self, partial_name=None):
        query = BusinessPage.select(fn.count(BusinessPage.id))
        if partial_name:
            query = query.where(fn.LOWER(BusinessPage.name).contains(partial_name.lower()))
        return query.scalar()


@service
class CampaignService:
    def __init__(
        self,
        ad_cabinet_service: AdCabinetService,
        executor_service: ExecutorService,
        business_page_service: BusinessPageService,
        core_campaign_service: CoreCampaignService,
    ):
        self.ad_cabinet_service = ad_cabinet_service
        self.executor_service = executor_service
        self.business_page_service = business_page_service
        self.core_campaign_service = core_campaign_service

    def get(self, id):
        try:
            return Campaign.get_by_id(id)
        except Campaign.DoesNotExist as exc:
            raise DoesNotExistError() from exc

    def list(self, page, page_size, sort_by, sort_order):
        order_by = getattr(Campaign, sort_by)
        if sort_order == SortOrder.desc:
            order_by = order_by.desc()

        return [ac for ac in Campaign.select().order_by(order_by).limit(page_size).offset(page - 1)]

    def create(
        self,
        name,
        ad_cabinet_id,
        executor_id,
        business_page_id,
        cost_model,
        cost_value,
        currency,
        status_mapper,
    ):
        core_campaign = self.core_campaign_service.create(
            name,
            cost_model,
            cost_value,
            currency,
            status_mapper=status_mapper,
        )

        ad_cabinet = self.ad_cabinet_service.get(ad_cabinet_id)
        executor = self.executor_service.get(executor_id)
        business_page = self.business_page_service.get(business_page_id)

        campaign = Campaign(
            core_campaign=core_campaign,
            ad_cabinet=ad_cabinet,
            executor=executor,
            business_page=business_page,
        )
        campaign.save()
        return campaign

    def update(
        self,
        campaign_id,
        name=None,
        cost_model=None,
        cost_value=None,
        currency=None,
        status_mapper=None,
        ad_cabinet_id=None,
        executor_id=None,
        business_page_id=None,
    ):
        campaign = self.get(campaign_id)

        self.core_campaign_service.update(
            campaign.core_campaign.id,
            name,
            cost_model,
            cost_value,
            currency,
            status_mapper,
        )

        if ad_cabinet_id:
            ad_cabinet = self.ad_cabinet_service.get(ad_cabinet_id)
            campaign.ad_cabinet = ad_cabinet

        if executor_id:
            executor = self.executor_service.get(executor_id)
            campaign.executor = executor

        if business_page_id:
            business_page = self.business_page_service.get(business_page_id)
            campaign.business_page = business_page

        campaign.save()
        return campaign

    def count(self):
        return Campaign.select(fn.count(Campaign.id)).scalar()
