from marshmallow import INCLUDE, fields

from src.core.schemas import Schema


class TrackClickRequestSchema(Schema):
    click_id = fields.UUID(required=True)
    campaign_id = fields.Integer(required=True)

    class Meta:
        unknown = INCLUDE


class TrackPostbackRequestSchema(Schema):
    click_id = fields.UUID(required=True)

    class Meta:
        unknown = INCLUDE


class TrackRedirectRequestSchema(Schema):
    click_id = fields.UUID(required=True)

    class Meta:
        unknown = INCLUDE
