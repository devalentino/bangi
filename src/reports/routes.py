import humps
from flask.views import MethodView

from src.auth import auth
from src.blueprint import Blueprint
from src.container import container
from src.reports.schemas import (
    BaseReportRequest,
    BaseReportResponse,
    ExpensesReportCreateRequest,
    ExpensesReportListResponse,
    ExpensesReportRequestSchema,
)
from src.reports.services import ReportService

blueprint = Blueprint('reports', __name__, description='Reports')


@blueprint.route('/statistics')
class StatisticsReport(MethodView):
    @blueprint.arguments(BaseReportRequest, location='query')
    @blueprint.response(200, BaseReportResponse)
    @auth.login_required
    def get(self, params):
        report_service = container.get(ReportService)
        report, available_parameters = report_service.base_report(
            {
                'campaign_id': params['campaignId'],
                'period_start': params['periodStart'],
                'period_end': params['periodEnd'],
                'group_parameters': params['groupParameters'],
            }
        )
        return {'content': {'report': report, 'parameters': available_parameters}}


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
            params.get('start'),
            params.get('end'),
        )
        return {
            'content': expenses,
            'pagination': params | {'total': total},
            'filters': {
                'start': params.get('start'),
                'end': params.get('end'),
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
