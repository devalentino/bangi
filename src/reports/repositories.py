from datetime import datetime
from typing import Annotated

from pymysql.converters import escape_string
from wireup import Inject, service

from peewee import JOIN, Case, MySQLDatabase, fn
from src.core.enums import LeadStatus
from src.reports.entities import Expense
from src.tracker.entities import TrackClick, TrackPostback


@service
class StatisticsReportRepository:
    def __init__(self, database: MySQLDatabase, gap_seconds: Annotated[str, Inject(param='REPORT_GAP_SECONDS')]):
        self.database = database
        self.gap_seconds = gap_seconds

    def _leads_statistics(self, parameters):
        status = fn.json_value(TrackPostback.parameters, '$.status')
        cost_value = Case(
            None, [((status == LeadStatus.accept.value) | (status == LeadStatus.expect), TrackPostback.cost_value)], 0
        )

        leads_subquery = TrackPostback.select(
            TrackPostback.click_id,
            status.alias('status'),
            fn.row_number()
            .over(partition_by=TrackPostback.click_id, order_by=TrackPostback.id.desc())
            .alias('row_number'),
            cost_value.alias('cost_value'),
        ).where(TrackPostback.created_at >= parameters['period_start'] - self.gap_seconds)

        if 'period_end' in parameters:
            leads_subquery = leads_subquery.where(
                TrackPostback.created_at < parameters['period_end'] + self.gap_seconds
            )

        date = fn.date(fn.from_unixtime(TrackClick.created_at)).alias('date')
        lead_status = leads_subquery.c.status.alias('lead_status')

        select = [
            fn.COUNT(TrackClick.click_id).alias('clicks_count'),
            fn.COUNT(leads_subquery.c.click_id).alias('leads_count'),
            fn.SUM(leads_subquery.c.cost_value).alias('payouts'),
            lead_status,
            date,
        ]

        group_by = [date, lead_status]
        if 'group_parameters' in parameters:
            for group_parameter in parameters['group_parameters']:
                path = f'$.{escape_string(group_parameter)}'
                parameter = fn.json_value(TrackClick.parameters, path).alias(group_parameter)
                select.append(parameter)
                group_by.append(parameter)

        query = (
            TrackClick.select(*select)
            .join(
                leads_subquery,
                JOIN.LEFT_OUTER,
                on=((TrackClick.click_id == leads_subquery.c.click_id) & (leads_subquery.c.row_number == 1)),
            )
            .where(
                (TrackClick.campaign_id == parameters['campaign_id'])
                & (TrackClick.created_at >= parameters['period_start'] - self.gap_seconds)
            )
        )

        if parameters['period_end']:
            query = query.where(TrackClick.created_at < parameters['period_end'] + self.gap_seconds)

        query = query.group_by(*group_by).order_by(date)

        cursor = self.database.execute(query)
        return cursor.fetchall()

    def _expenses(self, parameters):
        start = datetime.fromtimestamp(parameters['period_start']).date()
        query = Expense.select(Expense.date, Expense.distribution).where(
            (Expense.campaign_id == parameters['campaign_id']) & (Expense.date >= start)
        )

        if parameters['period_end']:
            end = datetime.fromtimestamp(parameters['period_end']).date()
            query = query.where(Expense.date <= end)

        cursor = self.database.execute(query)
        return cursor.fetchall()

    def _available_parameters(self, parameters):
        query = TrackClick.select(TrackClick.parameters).where(
            (TrackClick.campaign_id == parameters['campaign_id'])
            & (TrackClick.created_at >= parameters['period_start'])
        )

        if parameters['period_end']:
            query = query.where(TrackClick.created_at <= parameters['period_end'])

        query = query.order_by(TrackClick.id.desc()).limit(1)

        cursor = self.database.execute(query)
        return cursor.fetchone()

    def get(self, parameters):
        leads_statistics = self._leads_statistics(parameters)
        available_parameters = self._available_parameters(parameters)
        expenses = self._expenses(parameters)
        return leads_statistics, expenses, available_parameters
