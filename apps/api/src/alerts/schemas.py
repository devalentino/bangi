from marshmallow import fields

from src.core.schemas import Schema


class AlertResponseSchema(Schema):
    code = fields.String(required=True)
    message = fields.String(required=True)
    severity = fields.String(required=True)
    source = fields.String(allow_none=True)
    payload = fields.Dict(required=True)


class AlertListResponseSchema(Schema):
    content = fields.Nested(AlertResponseSchema(many=True), required=True)
