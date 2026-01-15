from playhouse.shortcuts import model_to_dict

from peewee import BooleanField, CharField, ForeignKeyField, ManyToManyField, TimestampField
from src.core.entities import Campaign as CoreCampaign
from src.core.entities import Entity

TABLE_NAME_PREFIX = 'facebook_autoregs_'


class Executor(Entity):
    name = CharField()
    is_banned = BooleanField()

    class Meta:
        table_name = f'{TABLE_NAME_PREFIX}executor'


class BusinessPortfolio(Entity):
    name = CharField()
    is_banned = BooleanField()
    executors = ManyToManyField(Executor, backref='executors')

    class Meta:
        table_name = f'{TABLE_NAME_PREFIX}business_portfolio'

    def to_dict(self):
        return model_to_dict(self) | {
            'executors': [e.to_dict() for e in self.executors],
            'ad_cabinets': [ac.to_dict() for ac in self.ad_cabinets],
        }


class AdCabinet(Entity):
    name = CharField()
    is_banned = BooleanField()
    business_portfolio = ForeignKeyField(BusinessPortfolio, backref='ad_cabinets', null=True)

    class Meta:
        table_name = f'{TABLE_NAME_PREFIX}ad_cabinet'

    def to_dict(self):
        business_portfolio_dict = None
        if self.business_portfolio:
            business_portfolio_dict = {
                'id': self.business_portfolio.id,
                'name': self.business_portfolio.name,
                'is_banned': self.business_portfolio.is_banned,
            }

        return model_to_dict(self) | {'business_portfolio': business_portfolio_dict}


class BusinessPage(Entity):
    name = CharField()
    is_banned = BooleanField()

    class Meta:
        table_name = f'{TABLE_NAME_PREFIX}business_page'


class Campaign(Entity):
    core_campaign = ForeignKeyField(CoreCampaign, backref='core_campaign')
    ad_cabinet = ForeignKeyField(AdCabinet, backref='ad_cabinet')
    executor = ForeignKeyField(Executor, backref='executor')
    business_page = ForeignKeyField(BusinessPage, backref='business_page')

    class Meta:
        table_name = f'{TABLE_NAME_PREFIX}ad_campaign'


class BusinessPortfolioAccessUrl(Entity):
    business_portfolio = ForeignKeyField(BusinessPortfolio, backref='access_urls', null=True)
    url = CharField()
    expires_at = TimestampField(null=True, utc=True)

    class Meta:
        table_name = f'{TABLE_NAME_PREFIX}business_portfolio_access_url'


BusinessPortfolioExecutor = BusinessPortfolio.executors.get_through_model()
BusinessPortfolioExecutor._meta.table_name = f'{TABLE_NAME_PREFIX}business_portfolio2executor'
