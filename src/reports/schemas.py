from marshmallow import INCLUDE, fields

from src.core.schemas import ComaSeparatedStringsField, PaginationRequestSchema, PaginationResponseSchema, Schema
from src.reports.enums import ExpenseSortBy


class BaseReportRequest(Schema):
    campaignId = fields.Integer(required=True)
    periodStart = fields.Integer(required=True)
    periodEnd = fields.Integer(required=False)
    groupParameters = ComaSeparatedStringsField(dump_default=[], load_default=[])

    class Meta:
        unknown = INCLUDE


class BaseReportContent(Schema):
    report = fields.List(fields.Dict, required=True)
    parameters = fields.List(fields.String)


class BaseReportResponse(Schema):
    content = fields.Nested(BaseReportContent())


class ExpensesReportDistribution(Schema):
    date = fields.Date(required=True)
    distribution = fields.Dict()


class ExpensesReportCreateRequest(Schema):
    campaignId = fields.Integer(required=True)
    distributionParameter = fields.String(required=True)
    dates = fields.Nested(ExpensesReportDistribution(many=True), required=True)


class ExpensesReportFilterSchema(Schema):
    start = fields.Date(required=False)
    end = fields.Date(required=False)
    campaignId = fields.Integer(required=True)


class ExpensesReportRequestSchema(PaginationRequestSchema, ExpensesReportFilterSchema):
    sortBy = fields.Enum(ExpenseSortBy, dump_default=ExpenseSortBy.date, load_default=ExpenseSortBy.id)


class ExpensesReportResponseItem(Schema):
    date = fields.Date(required=True)
    distribution = fields.Dict(required=True)


class ExpensesReportListResponse(Schema):
    content = fields.Nested(ExpensesReportResponseItem(many=True), required=True)
    pagination = fields.Nested(PaginationResponseSchema, required=True)
    filters = fields.Nested(ExpensesReportFilterSchema, required=True)
