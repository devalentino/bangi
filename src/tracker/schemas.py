from marshmallow import INCLUDE, Schema, fields


class TrackClickRequestSchema(Schema):
    click_id = fields.UUID(required=True)
    campaign_id = fields.Integer(required=True)
    parameters = fields.Dict()

    class Meta:
        unknown = INCLUDE
