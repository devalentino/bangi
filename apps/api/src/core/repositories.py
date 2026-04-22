from peewee import JOIN, SQL, fn
from wireup import injectable

from src.core.entities import Campaign
from src.core.enums import SortOrder
from src.tracker.entities import TrackClick


@injectable
class CampaignRepository:
    def get(self, campaign_id):
        return self._campaigns_with_summary().where(Campaign.id == campaign_id).get_or_none()

    def list(self, page, page_size, sort_by, sort_order):
        query = self._campaigns_with_summary()

        if sort_by in {'click_count', 'click_share'}:
            order_by = SQL('click_count')
        elif sort_by == 'last_activity_at':
            order_by = SQL('last_activity_at')
        else:
            order_by = getattr(Campaign, sort_by)

        if sort_order == SortOrder.desc:
            order_by = order_by.desc()
        else:
            order_by = order_by.asc()

        return list(query.order_by(order_by, Campaign.id).limit(page_size).offset((page - 1) * page_size).dicts())

    def all(self):
        return [campaign for campaign in Campaign.select()]

    def count(self):
        return Campaign.select(fn.count(Campaign.id)).scalar()

    def total_click_count(self):
        return TrackClick.select(fn.COUNT(TrackClick.id)).scalar()

    def _campaigns_with_summary(self):
        clicks_subquery = (
            TrackClick.select(
                TrackClick.campaign_id.alias('campaign_id'),
                fn.COUNT(TrackClick.id).alias('click_count'),
                fn.MAX(TrackClick.created_at).alias('last_activity_at'),
            )
            .group_by(TrackClick.campaign_id)
            .alias('clicks_summary')
        )

        return Campaign.select(
            Campaign,
            fn.COALESCE(clicks_subquery.c.click_count, 0).alias('click_count'),
            clicks_subquery.c.last_activity_at.alias('last_activity_at'),
        ).join(
            clicks_subquery,
            JOIN.LEFT_OUTER,
            on=(Campaign.id == clicks_subquery.c.campaign_id),
        )
