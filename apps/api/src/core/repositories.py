from peewee import JOIN, SQL, fn
from wireup import injectable

from src.core.entities import Campaign
from src.core.enums import SortOrder
from src.tracker.entities import TrackClick


@injectable
class CampaignRepository:
    def list(self, page, page_size, sort_by, sort_order):
        query = Campaign.select()

        if sort_by in {'click_count', 'click_share'}:
            query = self._campaigns_with_click_stats()
            order_by = SQL('click_count')
        elif sort_by == 'last_activity_at':
            query = self._campaigns_with_click_stats()
            order_by = SQL('last_activity_at')
        else:
            order_by = getattr(Campaign, sort_by)

        if sort_order == SortOrder.desc:
            order_by = order_by.desc()
        else:
            order_by = order_by.asc()

        return list(query.order_by(order_by, Campaign.id).limit(page_size).offset((page - 1) * page_size))

    def all(self):
        return [campaign for campaign in Campaign.select()]

    def count(self):
        return Campaign.select(fn.count(Campaign.id)).scalar()

    def total_click_count(self):
        return TrackClick.select(fn.COUNT(TrackClick.id)).scalar()

    def get_click_stats(self, campaign_ids):
        if len(campaign_ids) == 0:
            return {}

        return {
            stats['campaign_id']: {
                'click_count': stats['click_count'],
                'last_activity_at': stats['last_activity_at'],
            }
            for stats in (
                TrackClick.select(
                    TrackClick.campaign_id.alias('campaign_id'),
                    fn.COUNT(TrackClick.id).alias('click_count'),
                    fn.MAX(TrackClick.created_at).alias('last_activity_at'),
                )
                .where(TrackClick.campaign_id.in_(campaign_ids))
                .group_by(TrackClick.campaign_id)
                .dicts()
            )
        }

    def _campaigns_with_click_stats(self):
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
