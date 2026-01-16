from flask.views import MethodView

from src.auth import auth
from src.blueprint import Blueprint
from src.container import container
from src.reports.schemas import BaseReportRequest, BaseReportResponse
from src.reports.services import ReportService

blueprint = Blueprint('reports', __name__, description='Reports')


@blueprint.route('/base')
class Report(MethodView):
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
