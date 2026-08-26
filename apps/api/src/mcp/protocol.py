from marshmallow_jsonschema import JSONSchema

from src.mcp.schemas import (
    CampaignListArgumentsSchema,
    CampaignStatisticsArgumentsSchema,
    SearchNotesArgumentsSchema,
    StoreAnalysisNoteArgumentsSchema,
    SummaryArgumentsSchema,
)

SUPPORTED_PROTOCOL_VERSIONS = {'2026-07-28'}

INSTRUCTIONS = (
    'Whenever discussing or analyzing a campaign with the user, start the conversation by calling the '
    'summary tool — it is the only tool that surfaces active alerts, so calling it first ensures the '
    'user is warned about risks before any analysis begins.\n\n'
    'Before every response you give the user during a campaign-analysis conversation, call '
    'store_analysis_note with a complete summary of the conversation so far — reasoning, data points '
    'considered, and hypotheses discussed, not just the final conclusion. On the first call in a '
    'conversation, omit session_handle. On every subsequent call, pass back exactly the session_handle '
    'value received from the previous call.\n\n'
    "When searching past notes with search_notes, write a query describing what you're looking for — "
    'a campaign name, a geo, a topic — rather than assuming it only works for the current campaign.'
)


json_schema_dumper = JSONSchema()


def schema_to_json_schema(schema_class):
    schema = schema_class()
    return json_schema_dumper.dump(schema)['definitions'][schema_class.__name__]


TOOL_DEFINITIONS = [
    {
        'name': 'summary',
        'description': (
            'Campaigns with activity in the last 7 days, together with the current alert feed. '
            'The entry point for any campaign-analysis conversation.'
        ),
        'inputSchema': schema_to_json_schema(SummaryArgumentsSchema),
    },
    {
        'name': 'campaign_list',
        'description': 'Paginated list of all campaigns on this Bangi instance, active or dormant.',
        'inputSchema': schema_to_json_schema(CampaignListArgumentsSchema),
    },
    {
        'name': 'campaign_statistics',
        'description': 'The statistics report for one campaign over a period, matching the Bangi dashboard.',
        'inputSchema': schema_to_json_schema(CampaignStatisticsArgumentsSchema),
    },
    {
        'name': 'store_analysis_note',
        'description': 'Persist a running summary of the current analysis conversation.',
        'inputSchema': schema_to_json_schema(StoreAnalysisNoteArgumentsSchema),
    },
    {
        'name': 'search_notes',
        'description': 'Search stored conversation summaries by semantic similarity to a free-text query.',
        'inputSchema': schema_to_json_schema(SearchNotesArgumentsSchema),
    },
]


class ProtocolError(Exception):
    def __init__(self, code, message, http_status=400):
        self.code = code
        self.message = message
        self.http_status = http_status


def validate_headers(headers, body):
    if headers.get('MCP-Protocol-Version') not in SUPPORTED_PROTOCOL_VERSIONS:
        raise ProtocolError(-32020, 'HeaderMismatch')

    if body['method'] == 'tools/call':
        if headers.get('Mcp-Method') != body['method']:
            raise ProtocolError(-32020, 'HeaderMismatch')
        if headers.get('Mcp-Name') != body['params'].get('name'):
            raise ProtocolError(-32020, 'HeaderMismatch')


def discover_response():
    return {
        'protocolVersions': list(SUPPORTED_PROTOCOL_VERSIONS),
        'capabilities': {'tools': {'listChanged': False}},
        'instructions': INSTRUCTIONS,
    }


def list_tools_response():
    return {'tools': TOOL_DEFINITIONS}


def error_response(error):
    return {'error': {'code': error.code, 'message': error.message}}, error.http_status
