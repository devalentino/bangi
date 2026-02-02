from marshmallow import INCLUDE, fields

from src.core.schemas import Schema


class TrackClickRequestSchema(Schema):
    clickId = fields.UUID(required=True)
    campaignId = fields.Integer(required=True)

    class Meta:
        unknown = INCLUDE


class TrackPostbackRequestSchema(Schema):
    clickId = fields.UUID(required=True)

    class Meta:
        unknown = INCLUDE


class TrackProcessRequestSchema(Schema):
    clickId = fields.String(required=False)

    class Meta:
        unknown = INCLUDE
