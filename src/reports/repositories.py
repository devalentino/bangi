from datetime import datetime, time
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

    @staticmethod
    def _period_timestamps(parameters):
        period_start = parameters['period_start']
        period_end = parameters.get('period_end')
        period_start_timestamp = datetime.combine(period_start, time.min).timestamp()
        period_end_timestamp = None
        if period_end:
            period_end_timestamp = datetime.combine(period_end, time.max).timestamp()

        return period_start_timestamp, period_end_timestamp

    def _leads_statistics(self, parameters):
        period_start_timestamp, period_end_timestamp = self._period_timestamps(parameters)
        cost_value = Case(
            None,
            [
                (
                    (TrackPostback.status == LeadStatus.accept.value) | (TrackPostback.status == LeadStatus.expect),
                    TrackPostback.cost_value,
                )
            ],
            0,
        )

        leads_subquery = TrackPostback.select(
            TrackPostback.click_id,
            TrackPostback.status,
            fn.row_number()
            .over(partition_by=TrackPostback.click_id, order_by=TrackPostback.id.desc())
            .alias('row_number'),
            cost_value.alias('cost_value'),
        ).where(TrackPostback.created_at >= period_start_timestamp - self.gap_seconds)

        if period_end_timestamp:
            leads_subquery = leads_subquery.where(TrackPostback.created_at < period_end_timestamp + self.gap_seconds)

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
                & (TrackClick.created_at >= period_start_timestamp - self.gap_seconds)
            )
        )

        if period_end_timestamp:
            query = query.where(TrackClick.created_at < period_end_timestamp + self.gap_seconds)

        if parameters.get('skip_clicks_without_parameters'):
            query = query.where(fn.json_length(TrackClick.parameters) > 0)

        query = query.group_by(*group_by).order_by(date)

        cursor = self.database.execute(query)
        return cursor.fetchall()

    def _expenses(self, parameters):
        query = Expense.select(Expense.date, Expense.distribution).where(
            (Expense.campaign_id == parameters['campaign_id']) & (Expense.date >= parameters['period_start'])
        )

        if parameters['period_end']:
            query = query.where(Expense.date <= parameters['period_end'])

        cursor = self.database.execute(query)
        return cursor.fetchall()

    def _available_parameters(self, parameters):
        period_start_timestamp, period_end_timestamp = self._period_timestamps(parameters)
        query = TrackClick.select(TrackClick.parameters).where(
            (TrackClick.campaign_id == parameters['campaign_id']) & (TrackClick.created_at >= period_start_timestamp)
        )

        if period_end_timestamp:
            query = query.where(TrackClick.created_at <= period_end_timestamp)

        query = query.order_by(TrackClick.id.desc()).limit(1)

        cursor = self.database.execute(query)
        return cursor.fetchone()

    def get(self, parameters):
        leads_statistics = self._leads_statistics(parameters)
        available_parameters = self._available_parameters(parameters)
        expenses = self._expenses(parameters)
        return leads_statistics, expenses, available_parameters

    def get_distribution_values(self, parameters):
        period_start_timestamp, period_end_timestamp = self._period_timestamps(parameters)

        group_values = [fn.json_value(TrackClick.parameters, f'$.{p}').alias(p) for p in parameters['group_parameters']]

        query = TrackClick.select(*group_values).where(
            (TrackClick.campaign_id == parameters['campaign_id']) & (TrackClick.created_at >= period_start_timestamp)
        )

        if period_end_timestamp:
            query = query.where(TrackClick.created_at <= period_end_timestamp)

        query = query.group_by(*group_values)
        cursor = self.database.execute(query)
        return cursor.fetchall()
