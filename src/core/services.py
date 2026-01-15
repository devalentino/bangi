from wireup import service

from peewee import fn
from src.core.entities import Campaign
from src.core.enums import SortOrder


@service
class CampaignService:
    def get(self, id):
        return Campaign.get_by_id(id)

    def list(self, page, page_size, sort_by, sort_order):
        order_by = getattr(Campaign, sort_by)
        if sort_order == SortOrder.desc:
            order_by = order_by.desc()

        return [c for c in Campaign.select().order_by(order_by).limit(page_size).offset(page - 1)]

    def all(self):
        return [c for c in Campaign.select()]

    def create(self, name, cost_model, cost_value, currency):
        campaign = Campaign(name=name, cost_model=cost_model, cost_value=cost_value, currency=currency)
        campaign.save()
        return campaign

    def update(self, campaign_id, name=None, cost_model=None, cost_value=None, currency=None):
        campaign = Campaign.get_by_id(campaign_id)

        if name:
            campaign.name = name

        if cost_model:
            campaign.cost_model = cost_model

        if cost_value:
            campaign.cost_value = cost_value

        if currency:
            campaign.currency = currency

        campaign.save()

        return campaign

    def count(self):
        return Campaign.select(fn.count(Campaign.id)).scalar()
