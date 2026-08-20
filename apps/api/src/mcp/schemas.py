from marshmallow import fields

from src.core.constants import PAGINATION_DEFAULT_PAGE_SIZE
from src.core.schemas import PaginationRequestSchema, Schema


class JsonRpcRequestSchema(Schema):
    jsonrpc = fields.String(required=True)
    id = fields.Raw(allow_none=True, load_default=None)
    method = fields.String(required=True)
    params = fields.Dict(load_default=dict)


class SummaryArgumentsSchema(Schema):
    page = fields.Integer(load_default=1)
    pageSize = fields.Integer(load_default=PAGINATION_DEFAULT_PAGE_SIZE)


class CampaignListArgumentsSchema(PaginationRequestSchema):
    pass


class CampaignStatisticsArgumentsSchema(Schema):
    campaignId = fields.Integer(required=True)
    periodStart = fields.Date(required=True)
    periodEnd = fields.Date(required=False)
    groupParameters = fields.List(fields.String(), dump_default=[], load_default=[])


class StoreAnalysisNoteArgumentsSchema(Schema):
    summary = fields.String(required=True)
    sessionId = fields.String(required=False, allow_none=True, load_default=None)


class SearchNotesArgumentsSchema(Schema):
    query = fields.String(required=True)
