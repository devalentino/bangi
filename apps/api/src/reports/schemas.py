from marshmallow import INCLUDE, fields

from src.core.schemas import ComaSeparatedStringsField, PaginationRequestSchema, PaginationResponseSchema, Schema
from src.reports.enums import DiscardGroupBy, DiscardWindow, ExpenseSortBy


class StatisticsReportRequest(Schema):
    campaignId = fields.Integer(required=True)
    periodStart = fields.Date(required=True)
    periodEnd = fields.Date(required=False)
    groupParameters = ComaSeparatedStringsField(dump_default=[], load_default=[])
    skipClicksWithoutParameters = fields.Boolean(dump_default=False, load_default=False)

    class Meta:
        unknown = INCLUDE


class StatisticsReportContent(Schema):
    report = fields.Dict()
    total = fields.Dict()
    parameters = fields.List(fields.String)
    groupParameters = fields.List(fields.String)


class StatisticsReportResponse(Schema):
    content = fields.Nested(StatisticsReportContent())


class ExpensesReportDistribution(Schema):
    date = fields.Date(required=True)
    distribution = fields.Dict()


class ExpensesReportCreateRequest(Schema):
    campaignId = fields.Integer(required=True)
    distributionParameter = fields.String(required=True)
    dates = fields.Nested(ExpensesReportDistribution(many=True), required=True)


class ExpensesReportFilterSchema(Schema):
    periodStart = fields.Date(required=False)
    periodEnd = fields.Date(required=False)
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


class ExpensesDistributionParametersRequestSchema(Schema):
    campaignId = fields.Integer(required=True)


class ExpensesDistributionParametersResponseSchema(Schema):
    parameter = fields.String(required=True)


class ExpensesDistributionParameterValuesRequestSchema(Schema):
    campaignId = fields.Integer(required=True)
    parameter = fields.String(required=True)


class ExpensesDistributionParameterValuesResponseSchema(Schema):
    value = fields.String(required=True)


class PostbacksReportFilterSchema(Schema):
    campaignId = fields.Integer(required=True)


class PostbacksReportRequestSchema(PaginationRequestSchema, PostbacksReportFilterSchema):
    pass


class LeadReportResponseListItem(Schema):
    clickId = fields.UUID(required=True)
    status = fields.String(allow_none=True)
    costValue = fields.Decimal(places=2, allow_none=True)
    currency = fields.String(allow_none=True)
    createdAt = fields.Integer(required=True)


class LeadReportListResponse(Schema):
    content = fields.Nested(LeadReportResponseListItem(many=True), required=True)
    pagination = fields.Nested(PaginationResponseSchema, required=True)
    filters = fields.Nested(PostbacksReportFilterSchema, required=True)


class LeadResponsePostbackItem(Schema):
    parameters = fields.Dict(required=True)
    status = fields.String(allow_none=True)
    costValue = fields.Decimal(places=2, allow_none=True)
    currency = fields.String(allow_none=True)
    createdAt = fields.Integer(required=True)


class LeadResponseLeadItem(Schema):
    parameters = fields.Dict(required=True)
    createdAt = fields.Integer(required=True)


class LeadResponseSchema(Schema):
    clickId = fields.UUID(required=True)
    campaignId = fields.Integer(required=True)
    campaignName = fields.String(required=True)
    parameters = fields.Dict(required=True)
    createdAt = fields.Integer(required=True)
    leads = fields.Nested(LeadResponseLeadItem(many=True), required=True)
    postbacks = fields.Nested(LeadResponsePostbackItem(many=True), required=True)


class DiscardReportRequestSchema(Schema):
    campaignId = fields.Integer(required=True)
    window = fields.Enum(DiscardWindow, required=True)
    groupBy = fields.Enum(DiscardGroupBy, required=True)


class DiscardReportTotalsSchema(Schema):
    discardCount = fields.Integer(required=True)
    totalCount = fields.Integer(required=True)
    rate = fields.Float(required=True)
    eligible = fields.Boolean(required=True)


class DiscardReportRowSchema(Schema):
    value = fields.Raw(required=True, allow_none=True)
    count = fields.Integer(required=True)
    share = fields.Float(required=True)


class DiscardReportFilterSchema(Schema):
    campaignId = fields.Integer(required=True)
    window = fields.String(required=True)
    groupBy = fields.String(required=True)


class DiscardReportResponseSchema(Schema):
    content = fields.Nested(DiscardReportRowSchema(many=True), required=True)
    summary = fields.Nested(DiscardReportTotalsSchema(), required=True)
    filters = fields.Nested(DiscardReportFilterSchema(), required=True)
