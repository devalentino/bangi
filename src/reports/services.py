import json
from collections import defaultdict
from datetime import datetime, time, timedelta

from wireup import service

from src.core.entities import Campaign
from src.core.enums import LeadStatus, SortOrder
from src.core.services import CampaignService
from src.core.utils import utcnow
from src.reports.entities import Expense
from src.reports.exceptions import ExpensesDistributionParameterError
from src.reports.repositories import StatisticsReportRepository
from src.tracker.entities import TrackClick
from src.tracker.services import TrackService


@service
class ReportService:
    def __init__(
        self,
        campaign_service: CampaignService,
        track_service: TrackService,
        statistics_report_repository: StatisticsReportRepository,
    ):
        self.campaign_service = campaign_service
        self.track_service = track_service
        self.statistics_report_repository = statistics_report_repository

    def _get_payouts(self, statistics_container, group_parameters):
        if len(group_parameters) > 0:
            payouts_accepted_sum = 0
            payouts_expected_sum = 0

            for stats in statistics_container.values():
                payouts_accepted, payouts_expected = self._get_payouts(stats, group_parameters[1:])
                payouts_accepted_sum += payouts_accepted
                payouts_expected_sum += payouts_expected

            return payouts_accepted_sum, payouts_expected_sum

        payouts_accepted = sum(
            stats['payouts']
            for status, stats in statistics_container['statuses'].items()
            if status == LeadStatus.accept
        )
        payouts_expected = sum(
            stats['payouts']
            for status, stats in statistics_container['statuses'].items()
            if status in {LeadStatus.accept, LeadStatus.expect}
        )

        return payouts_accepted, payouts_expected

    def _fill_clicks(self, statistics_container, group_parameters, clicks_count, leads_count, payouts, lead_status):
        if len(group_parameters) == 0:
            statistics_container.setdefault('statuses', {})
            statistics_container.setdefault('clicks', 0)

            statistics_container['clicks'] += clicks_count
            if lead_status:
                statistics_container['statuses'][lead_status] = {'leads': leads_count, 'payouts': payouts or 0}

            return

        group_parameter = group_parameters[0]
        statistics_container.setdefault(group_parameter, {})
        self._fill_clicks(
            statistics_container[group_parameter], group_parameters[1:], clicks_count, leads_count, payouts, lead_status
        )

    def _build_statistics_report(self, report_rows, expenses_rows, parameters, match_expenses_distribution):
        report = defaultdict(dict)

        for clicks_count, leads_count, payouts, lead_status, date, *parameters_values in report_rows:
            self._fill_clicks(report[date], parameters_values, clicks_count, leads_count, payouts, lead_status)

        date2distribution = {date: json.loads(distribution) for date, distribution in expenses_rows}

        period_start_date = datetime.fromtimestamp(parameters['period_start']).date()
        period_end_date = utcnow().date()
        if parameters['period_end']:
            period_end_date = datetime.fromtimestamp(parameters['period_end']).date()

        days_delta = period_end_date - period_start_date
        for day in range(days_delta.days + 1):
            date = period_start_date + timedelta(days=day)

            if date not in report:
                report[date] = {}

            # extend records with expenses
            if match_expenses_distribution:
                distribution = date2distribution.get(date)
                if distribution:
                    for distribution_value, expenses in distribution.items():
                        payouts_accepted, payouts_expected = self._get_payouts(
                            report[date][distribution_value], parameters['group_parameters'][1:]
                        )

                        report[date][distribution_value]['expenses'] = expenses
                        report[date][distribution_value]['roi_accepted'] = (
                            (float(payouts_accepted) - report[date][distribution_value]['expenses'])
                            / report[date][distribution_value]['expenses']
                            * 100
                        )
                        report[date][distribution_value]['roi_expected'] = (
                            (float(payouts_expected) - report[date][distribution_value]['expenses'])
                            / report[date][distribution_value]['expenses']
                            * 100
                        )
            else:
                distribution = date2distribution.get(date)
                if distribution:
                    payouts_accepted, payouts_expected = self._get_payouts(report[date], parameters['group_parameters'])

                    report[date]['expenses'] = sum(distribution.values())
                    report[date]['roi_accepted'] = (
                        (float(payouts_accepted) - report[date]['expenses']) / report[date]['expenses'] * 100
                    )
                    report[date]['roi_expected'] = (
                        (float(payouts_expected) - report[date]['expenses']) / report[date]['expenses'] * 100
                    )

        return report

    def statistics_report(self, parameters):
        campaign = self.campaign_service.get(parameters['campaign_id'])

        # make expenses_distribution_parameter in group parameters, expenses will be attached to same level
        group_parameters = [p for p in parameters['group_parameters'] if p != campaign.expenses_distribution_parameter]
        if campaign.expenses_distribution_parameter in parameters['group_parameters']:
            group_parameters.insert(0, campaign.expenses_distribution_parameter)
        parameters['group_parameters'] = group_parameters

        match_expenses_distribution = False
        if (
            len(parameters['group_parameters']) > 0
            and parameters['group_parameters'][0] == campaign.expenses_distribution_parameter
        ):
            match_expenses_distribution = True

        report_rows, expenses_rows, available_parameters_row = self.statistics_report_repository.get(parameters)
        report = self._build_statistics_report(report_rows, expenses_rows, parameters, match_expenses_distribution)

        available_parameters = []
        if available_parameters_row:
            (available_parameters_row,) = available_parameters_row
            available_parameters = list(json.loads(available_parameters_row).keys()) if available_parameters_row else []

        return report, available_parameters, group_parameters

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

        query = query.order_by(order_by).limit(page_size).offset((page - 1) * page_size)
        expenses = [e for e in query]
        if expenses:
            return expenses, total

        # cover case for no reports
        campaign = self.campaign_service.get(campaign_id)

        dates = self.track_service.get_click_dates(
            campaign.id,
            datetime.combine(period_start, time.min).timestamp(),
            datetime.combine(period_end, time.max).timestamp(),
        )
        if len(dates) == 0:
            dates = [datetime.today()]

        expenses = [Expense(campaign=campaign, date=d, distribution={}) for d in dates]

        return expenses, 0


@service
class ReportHelperService:
    def list_expenses_distribution_parameters(self, campaign_id):
        parameters = set()
        query = TrackClick.select(TrackClick.parameters).where(TrackClick.campaign_id == campaign_id)
        for click in query:
            if click.parameters:
                parameters.update(click.parameters.keys())

        return sorted(parameters)

    def list_expenses_distribution_parameter_values(self, campaign_id, parameter):
        values = set()
        query = TrackClick.select(TrackClick.parameters).where(TrackClick.campaign_id == campaign_id)
        for click in query:
            if not click.parameters or parameter not in click.parameters:
                continue
            value = click.parameters.get(parameter)
            values.add(value)

        return sorted(values)
