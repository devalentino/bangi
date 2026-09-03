import simplejson
from marshmallow_jsonschema import JSONSchema

from src.mcp.schemas import (
    CampaignListArgumentsSchema,
    CampaignStatisticsArgumentsSchema,
    SearchNotesArgumentsSchema,
    StoreAnalysisNoteArgumentsSchema,
    SummaryArgumentsSchema,
)

SUPPORTED_PROTOCOL_VERSIONS = {'2025-11-25', '2026-07-28'}

# 2026-07-28 removes the initialize handshake entirely, so a client speaking it never sends
# initialize — 2025-11-25 is the only supported version for which a handshake exists at all.
HANDSHAKE_PROTOCOL_VERSION = '2025-11-25'

INSTRUCTIONS = (
    'Whenever discussing or analyzing a campaign with the user, start the conversation by calling the '
    'summary tool — it is the only tool that surfaces active alerts, so calling it first ensures the '
    'user is warned about risks before any analysis begins.\n\n'
    'Before every response you give the user during a campaign-analysis conversation, call '
    'store_analysis_note with a complete summary of the conversation so far — reasoning, data points '
    'considered, and hypotheses discussed, not just the final conclusion. On the first call in a '
    'conversation, omit session_handle. On every subsequent call, pass back exactly the session_handle '
    'value received from the previous call. Starting a new session — omitting session_handle again — '
    'when you return to a campaign after a meaningful time gap (long enough that the underlying '
    'situation may have changed) is expected and correct; do not try to continue or recover an earlier '
    'session across such a gap.\n\n'
    'On every store_analysis_note call, pass campaignIds with the id(s) of whichever campaign(s) the '
    'running summary currently concerns. This set can grow or change across calls within a session as '
    "the conversation's scope evolves; pass an empty array only when the note is tied to no specific "
    'campaign. Independently of those tags, the summary text itself must name every campaign, creative, '
    'geo, or segment it refers to explicitly — never "the same campaign", "this campaign", "that ad", '
    'or "the same one". Each note has to be readable in isolation, months later, by an agent with no '
    'access to this conversation; the campaignIds tags do not make an ambiguous sentence inside the '
    'note self-explanatory.\n\n'
    "When searching past notes with search_notes, write a query describing what you're looking for — "
    'a campaign name, a geo, a topic — rather than assuming it only works for the current campaign. '
    'Pass campaignId to scope the search to notes tagged with one campaign; omit it to search every '
    'note. Each result carries its own campaignIds tags so you can tell which campaign(s) it belongs '
    'to.\n\n'
    'Before using groupParameters for a profit/cost-based segment decision, check expensesDistributionParameter '
    'for this campaign (from campaign_list/summary) to see which dimension, if any, carries real expense data. '
    'Only use a segment breakdown along that dimension as the basis for a cut/pause recommendation. A breakdown '
    'along any other dimension is a click/lead-quality signal only — say explicitly that real spend for that '
    "segment would need to be verified externally (e.g. in the traffic source's own reporting) before "
    'recommending a cut based on it.'
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
        'description': (
            'The statistics report for one campaign over a period, matching the Bangi dashboard. Supports '
            'breaking down the report by campaign-specific dimensions via groupParameters — see '
            "expensesDistributionParameter on the campaign's entry in campaign_list/summary to know which "
            'dimension (if any) returns a real expense breakdown for this campaign before drawing profit/ROI '
            'conclusions from any other breakdown.'
        ),
        'inputSchema': schema_to_json_schema(CampaignStatisticsArgumentsSchema),
    },
    {
        'name': 'store_analysis_note',
        'description': (
            'Persist a running summary of the current analysis conversation, tagged via campaignIds with '
            'the campaign(s) it concerns.'
        ),
        'inputSchema': schema_to_json_schema(StoreAnalysisNoteArgumentsSchema),
    },
    {
        'name': 'search_notes',
        'description': (
            'Search stored conversation summaries by semantic similarity to a free-text query, optionally '
            'scoped to a single campaign via campaignId.'
        ),
        'inputSchema': schema_to_json_schema(SearchNotesArgumentsSchema),
    },
]


class ProtocolError(Exception):
    def __init__(self, code, message, http_status=400):
        self.code = code
        self.message = message
        self.http_status = http_status


def validate_headers(headers, body):
    if body['method'] in ('initialize', 'notifications/initialized'):
        return

    if headers.get('MCP-Protocol-Version') not in SUPPORTED_PROTOCOL_VERSIONS:
        raise ProtocolError(-32020, 'HeaderMismatch')

    if body['method'] == 'tools/call':
        if headers.get('Mcp-Method') != body['method']:
            raise ProtocolError(-32020, 'HeaderMismatch')
        if headers.get('Mcp-Name') != body['params'].get('name'):
            raise ProtocolError(-32020, 'HeaderMismatch')


def initialize_response():
    return {
        'protocolVersion': HANDSHAKE_PROTOCOL_VERSION,
        'capabilities': {'tools': {'listChanged': False}},
        'serverInfo': {'name': 'bangi', 'version': '1.0.0'},
        'instructions': INSTRUCTIONS,
    }


def discover_response():
    return {
        'protocolVersions': sorted(SUPPORTED_PROTOCOL_VERSIONS),
        'capabilities': {'tools': {'listChanged': False}},
        'instructions': INSTRUCTIONS,
    }


def list_tools_response():
    return {'tools': TOOL_DEFINITIONS}


def tool_result(payload):
    # simplejson matches the app JSON provider (src/api.py), so Decimal report values
    # serialize the same way the enclosing response does.
    return {'content': [{'type': 'text', 'text': simplejson.dumps(payload)}]}


def success_response(request_id, result):
    return {'jsonrpc': '2.0', 'id': request_id, 'result': result}


def error_response(error, request_id=None):
    body = {'jsonrpc': '2.0', 'id': request_id, 'error': {'code': error.code, 'message': error.message}}
    return body, error.http_status
