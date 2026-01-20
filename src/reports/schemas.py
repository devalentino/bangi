from marshmallow import INCLUDE, fields

from src.core.schemas import ComaSeparatedStringsField, Schema


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
