import json
from datetime import datetime, timedelta

from wireup import service

from src.core.entities import Campaign
from src.core.enums import SortOrder
from src.core.services import CampaignService
from src.core.utils import utcnow
from src.reports.entities import Expense
from src.reports.exceptions import ExpensesDistributionParameterError
from src.reports.repositories import BaseReportRepository


@service
class ReportService:
    def __init__(
        self,
        campaign_service: CampaignService,
        base_report_repository: BaseReportRepository,
    ):
        self.campaign_service = campaign_service
        self.base_report_repository = base_report_repository

    def _build_base_report(self, report_rows, parameters):
        report = []
        for clicks_count, leads_count, lead_status, date, *parameters_values in report_rows:
            report.append(
                {
                    'date': date,
                    'clicks': clicks_count,
                    'leads': leads_count,
                    'lead_status': lead_status,
                    **dict(zip(parameters['group_parameters'], parameters_values)),
                }
            )

        period_start_date = datetime.fromtimestamp(parameters['period_start']).date()
        period_end_date = utcnow().date()
        if parameters['period_end']:
            period_end_date = datetime.fromtimestamp(parameters['period_end']).date()

        all_dates_report = []
        days_delta = period_end_date - period_start_date
        for day in range(days_delta.days + 1):
            date = (period_start_date + timedelta(days=day)).strftime('%Y-%m-%d')
            records = [r for r in report if r['date'] == date] or [{'date': date, 'clicks': 0}]
            all_dates_report.extend(records)

        return all_dates_report

    def base_report(self, parameters):
        report_rows, available_parameters_row = self.base_report_repository.get(parameters)
        report = self._build_base_report(report_rows, parameters)

        available_parameters = []
        if available_parameters_row:
            (available_parameters_row,) = available_parameters_row
            available_parameters = list(json.loads(available_parameters_row).keys()) if available_parameters_row else []

        return report, available_parameters

    def submit_expenses(self, campaign_id, expenses_distribution_parameter, date_distributions):
        campaign = self.campaign_service.get(campaign_id)
        if campaign.expenses_distribution_parameter is None:
            campaign.expenses_distribution_parameter = expenses_distribution_parameter
            campaign.save()

        if campaign.expenses_distribution_parameter != expenses_distribution_parameter:
            raise ExpensesDistributionParameterError()

        for date_distribution in date_distributions:
            Expense.insert(
                campaign=campaign,
                date=date_distribution['date'],
                distribution=date_distribution['distribution'],
            ).on_conflict(
                update={Expense.distribution: date_distribution['distribution']},
            ).execute()

    def list_expenses(self, page, page_size, sort_by, sort_order, campaign_id, period_start=None, period_end=None):
        order_by = getattr(Expense, sort_by)
        if sort_order == SortOrder.desc:
            order_by = order_by.desc()

        query = Expense.select(Expense, Campaign).join(Campaign).where(Expense.campaign == campaign_id)

        if period_start is not None:
            query = query.where(Expense.date >= period_start)

        if period_end is not None:
            query = query.where(Expense.date <= period_end)

        total = query.count()

        expenses = query.order_by(order_by).limit(page_size).offset((page - 1) * page_size)

        return [e for e in expenses], total
