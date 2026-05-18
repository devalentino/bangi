from marshmallow import INCLUDE, fields, pre_load

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


class TrackLeadRequestSchema(Schema):
    clickId = fields.UUID(required=True)

    class Meta:
        unknown = INCLUDE


class TrackProcessRequestSchema(Schema):
    clickId = fields.UUID(required=False)

    class Meta:
        unknown = INCLUDE


class TrackCurrentFlowCookieSchema(Schema):
    currentFlowId = fields.Integer(allow_none=True, load_default=None)

    @pre_load
    def normalize_current_flow_id(self, data, **kwargs):
        current_flow_id = data.get('currentFlowId')
        if current_flow_id is None:
            return data

        try:
            data['currentFlowId'] = int(current_flow_id)
        except (TypeError, ValueError):
            data['currentFlowId'] = None

        return data
