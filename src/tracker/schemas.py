from marshmallow import Schema, fields


class TrackClickRequestSchema(Schema):
    click_id = fields.UUID(required=True)
    campaign_name = fields.String()
    adset_name = fields.String()
    ad_name = fields.String()
    pixel = fields.String()
