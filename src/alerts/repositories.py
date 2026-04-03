from peewee import JOIN, Case, MySQLDatabase, fn
from wireup import injectable

from src.facebook_pacs.entities import BusinessPortfolio, BusinessPortfolioAccessUrl


@injectable
class BusinessPortfolioRepository:
    def __init__(self, database: MySQLDatabase):
        self.database = database

    def access_urls_expiration_statuses(self, threshold_already_expired, access_url_expiring_soon_days):

        threshold_expires_soon = threshold_already_expired + access_url_expiring_soon_days * 24 * 60 * 60

        expiration_status = Case(
            None,
            [
                (BusinessPortfolioAccessUrl.expires_at <= threshold_already_expired, 'already_expired'),
                (BusinessPortfolioAccessUrl.expires_at <= threshold_expires_soon, 'expires_soon'),
            ],
            'in_date',
        ).alias('expiration_status')

        expiration_statuses_subquery = BusinessPortfolio.select(
            BusinessPortfolio.id.alias('business_portfolio_id'),
            expiration_status,
        ).join(BusinessPortfolioAccessUrl)

        query = (
            BusinessPortfolio.select(
                BusinessPortfolio.id,
                BusinessPortfolio.name,
                expiration_statuses_subquery.c.expiration_status,
                fn.count(expiration_statuses_subquery.c.expiration_status).alias('expiration_status_count'),
            )
            .join(
                expiration_statuses_subquery,
                JOIN.LEFT_OUTER,
                on=(expiration_statuses_subquery.c.business_portfolio_id == BusinessPortfolio.id),
            )
            .group_by(
                BusinessPortfolio.id,
                BusinessPortfolio.name,
                expiration_statuses_subquery.c.expiration_status,
            )
        )

        cursor = self.database.execute(query)
        return cursor.fetchall()
