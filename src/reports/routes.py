import humps
from flask.views import MethodView

from src.auth import auth
from src.blueprint import Blueprint
from src.container import container
from src.reports.schemas import (
    ExpensesDistributionParametersRequestSchema,
    ExpensesDistributionParametersResponseSchema,
    ExpensesDistributionParameterValuesRequestSchema,
    ExpensesDistributionParameterValuesResponseSchema,
    ExpensesReportCreateRequest,
    ExpensesReportListResponse,
    ExpensesReportRequestSchema,
    StatisticsReportRequest,
    StatisticsReportResponse,
)
from src.reports.services import ReportHelperService, ReportService

blueprint = Blueprint('reports', __name__, description='Reports')


@blueprint.route('/statistics')
class StatisticsReport(MethodView):
    @blueprint.arguments(StatisticsReportRequest, location='query')
    @blueprint.response(200, StatisticsReportResponse)
    @auth.login_required
    def get(self, params):
        report_service = container.get(ReportService)
        report, available_parameters, group_parameters = report_service.statistics_report(
            {
                'campaign_id': params['campaignId'],
                'period_start': params['periodStart'],
                'period_end': params.get('periodEnd'),
                'group_parameters': params['groupParameters'],
            }
        )
        return {
            'content': {
                'report': {dt.isoformat(): stats for dt, stats in report.items()},
                'parameters': available_parameters,
                'groupParameters': group_parameters,
            }
        }


@blueprint.route('/expenses')
class ExpensesReport(MethodView):
    @blueprint.arguments(ExpensesReportRequestSchema, location='query')
    @blueprint.response(200, ExpensesReportListResponse)
    @auth.login_required
    def get(self, params):
        report_service = container.get(ReportService)
        expenses, total = report_service.list_expenses(
            params['page'],
            params['pageSize'],
            humps.decamelize(params['sortBy'].value),
            params['sortOrder'],
            params['campaignId'],
            params.get('periodStart'),
            params.get('periodEnd'),
        )
        return {
            'content': [e.to_dict() for e in expenses],
            'pagination': params | {'total': total},
            'filters': {
                'periodStart': params.get('periodStart'),
                'periodEnd': params.get('periodEnd'),
                'campaignId': params.get('campaignId'),
            },
        }

    @blueprint.arguments(ExpensesReportCreateRequest)
    @blueprint.response(200)
    @auth.login_required
    def post(self, expenses_payload):
        report_service = container.get(ReportService)
        report_service.submit_expenses(
            expenses_payload['campaignId'], expenses_payload['distributionParameter'], expenses_payload['dates']
        )


@blueprint.route('/helpers/expenses-distribution-parameters')
class FilterCampaignExpensesDistributionParameters(MethodView):
    @blueprint.arguments(ExpensesDistributionParametersRequestSchema, location='query')
    @blueprint.response(200, ExpensesDistributionParametersResponseSchema(many=True))
    @auth.login_required
    def get(self, params):
        helpers_service = container.get(ReportHelperService)
        parameters = helpers_service.list_expenses_distribution_parameters(params['campaignId'])
        return [{'parameter': p} for p in parameters]


@blueprint.route('/helpers/expenses-distribution-parameter-values')
class FilterCampaignExpensesDistributionParameterValues(MethodView):
    @blueprint.arguments(ExpensesDistributionParameterValuesRequestSchema, location='query')
    @blueprint.response(200, ExpensesDistributionParameterValuesResponseSchema(many=True))
    @auth.login_required
    def get(self, params):
        helpers_service = container.get(ReportHelperService)
        values = helpers_service.list_expenses_distribution_parameter_values(params['campaignId'], params['parameter'])
        return [{'value': v} for v in values]
