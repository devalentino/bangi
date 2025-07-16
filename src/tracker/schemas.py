from marshmallow import Schema, fields


class TrackClickRequestSchema(Schema):
    click_id = fields.UUID(required=True)
    campaign_id = fields.Integer(required=True)
    campaign_name = fields.String(required=True)
    adset_name = fields.String(required=True)
    ad_name = fields.String(required=True)
    pixel = fields.String(required=True)
