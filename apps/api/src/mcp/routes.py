import time
import uuid

import humps
from flask import Response, request
from flask.views import MethodView

from src.alerts.services import AlertService
from src.auth import token_auth
from src.container import container
from src.core.blueprint import Blueprint
from src.core.repositories import CampaignRepository
from src.mcp import protocol
from src.mcp.schemas import (
    CampaignListArgumentsSchema,
    CampaignStatisticsArgumentsSchema,
    JsonRpcRequestSchema,
    SearchNotesArgumentsSchema,
    StoreAnalysisNoteArgumentsSchema,
    SummaryArgumentsSchema,
)
from src.mcp.services import AgentNoteService, EmbeddingService
from src.reports.services import ReportService

blueprint = Blueprint('mcp', __name__, description='MCP')

_KNOWN_TOOL_NAMES = {tool['name'] for tool in protocol.TOOL_DEFINITIONS}

_SUMMARY_ACTIVITY_WINDOW_SECONDS = 7 * 24 * 60 * 60


@blueprint.route('', strict_slashes=False)
class Mcp(MethodView):
    @blueprint.arguments(JsonRpcRequestSchema)
    @blueprint.response(200)
    @token_auth.login_required
    def post(self, body):
        try:
            protocol.validate_headers(request.headers, body)
        except protocol.ProtocolError as error:
            return protocol.error_response(error)

        if body['method'] == 'initialize':
            return protocol.initialize_response()
        if body['method'] == 'notifications/initialized':
            return Response(status=202)
        if body['method'] == 'server/discover':
            return protocol.discover_response()
        if body['method'] == 'tools/list':
            return protocol.list_tools_response()
        if body['method'] == 'tools/call':
            return call_tool(body['params'])

        return protocol.error_response(protocol.ProtocolError(-32601, 'MethodNotFound', 404))


def call_tool(params):
    name = params.get('name')
    arguments = params.get('arguments', {})

    if name not in _KNOWN_TOOL_NAMES:
        return protocol.error_response(protocol.ProtocolError(-32602, 'InvalidParams', 400))

    if name == 'summary':
        return summary_tool(arguments)
    if name == 'campaign_list':
        return campaign_list_tool(arguments)
    if name == 'campaign_statistics':
        return campaign_statistics_tool(arguments)
    if name == 'store_analysis_note':
        return store_analysis_note_tool(arguments)
    if name == 'search_notes':
        return search_notes_tool(arguments)


def summary_tool(arguments):
    arguments = SummaryArgumentsSchema().load(arguments)
    campaign_repository = container.get(CampaignRepository)
    alert_service = container.get(AlertService)

    since = int(time.time()) - _SUMMARY_ACTIVITY_WINDOW_SECONDS
    campaigns = campaign_repository.list_with_recent_activity(since, arguments['page'], arguments['pageSize'])
    total = campaign_repository.count_with_recent_activity(since)
    click_stats = campaign_repository.get_click_stats([campaign.id for campaign in campaigns])
    total_click_count = campaign_repository.total_click_count()

    return {
        'content': [serialize_campaign(campaign, click_stats, total_click_count) for campaign in campaigns],
        'pagination': {'page': arguments['page'], 'pageSize': arguments['pageSize'], 'total': total},
        'alerts': alert_service.serialize(alert_service.collect(container)),
    }


def campaign_list_tool(arguments):
    arguments = CampaignListArgumentsSchema().load(arguments)
    campaign_repository = container.get(CampaignRepository)

    campaigns = campaign_repository.list(
        arguments['page'],
        arguments['pageSize'],
        humps.decamelize(arguments['sortBy'].value),
        arguments['sortOrder'],
    )
    total = campaign_repository.count()
    click_stats = campaign_repository.get_click_stats([campaign.id for campaign in campaigns])
    total_click_count = campaign_repository.total_click_count()

    return {
        'content': [serialize_campaign(campaign, click_stats, total_click_count) for campaign in campaigns],
        'pagination': {'page': arguments['page'], 'pageSize': arguments['pageSize'], 'total': total},
    }


def campaign_statistics_tool(arguments):
    arguments = CampaignStatisticsArgumentsSchema().load(arguments)
    report_service = container.get(ReportService)

    report, total, available_parameters, group_parameters = report_service.statistics_report(
        {
            'campaign_id': arguments['campaignId'],
            'period_start': arguments['periodStart'],
            'period_end': arguments.get('periodEnd'),
            'group_parameters': arguments['groupParameters'],
            'skip_clicks_without_parameters': False,
        }
    )

    return {
        'content': {
            'report': {dt.isoformat(): stats for dt, stats in report.items()},
            'total': total,
            'parameters': available_parameters,
            'groupParameters': group_parameters,
        }
    }


def store_analysis_note_tool(arguments):
    arguments = StoreAnalysisNoteArgumentsSchema().load(arguments)
    embedding_service = container.get(EmbeddingService)
    agent_note_service = container.get(AgentNoteService)

    session_id = arguments['sessionId'] or str(uuid.uuid4())
    embedding = embedding_service.compute(arguments['summary'])
    agent_note_service.upsert(session_id, arguments['summary'], embedding)

    return {'content': {'sessionId': session_id}}


def search_notes_tool(arguments):
    arguments = SearchNotesArgumentsSchema().load(arguments)
    embedding_service = container.get(EmbeddingService)
    agent_note_service = container.get(AgentNoteService)

    query_embedding = embedding_service.compute(arguments['query'])
    notes = agent_note_service.search(query_embedding)

    return {
        'content': [{'noteText': note['note_text'], 'updatedAt': int(note['updated_at'].timestamp())} for note in notes]
    }


def serialize_campaign(campaign, click_stats, total_click_count):
    stats = click_stats.get(campaign.id, {})
    click_count = stats.get('click_count', 0)
    last_activity_at = stats.get('last_activity_at')
    return {
        'id': campaign.id,
        'name': campaign.name,
        'summary': {
            'clickCount': click_count,
            'clickShare': click_count / total_click_count if total_click_count else 0.0,
            'lastActivityAt': int(last_activity_at.timestamp()) if last_activity_at else None,
        },
    }
