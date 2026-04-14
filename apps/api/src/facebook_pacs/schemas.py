import decimal

from marshmallow import fields, validates_schema

from src.core.enums import CostModel, Currency
from src.core.schemas import PaginationRequestSchema, PaginationResponseSchema, Schema, validate_status_mapper


class FacebookPacsNameFilterResponseSchema(Schema):
    partialName = fields.String(allow_none=True, required=True)


class FacebookPacsBusinessPortfolioNestedResponseSchema(Schema):
    id = fields.Integer(required=True)
    name = fields.String(required=True)
    isBanned = fields.Boolean(required=True)


class FacebookPacsExecutorRequestSchema(Schema):
    name = fields.String(required=True)
    isBanned = fields.Boolean(required=True)


class FacebookPacsExecutorResponseSchema(FacebookPacsExecutorRequestSchema):
    id = fields.Integer(required=True)


class FacebookPacsNameFilterRequestSchema(PaginationRequestSchema):
    partialName = fields.String(load_default=None)


class FacebookPacsAdCabinetRequestSchema(Schema):
    name = fields.String(required=True)
    isBanned = fields.Boolean(required=True)


class FacebookPacsAdCabinetResponseSchema(FacebookPacsAdCabinetRequestSchema):
    id = fields.Integer(required=True)
    businessPortfolio = fields.Nested(FacebookPacsBusinessPortfolioNestedResponseSchema())


class FacebookPacsAdCabinetListResponseSchema(Schema):
    content = fields.Nested(FacebookPacsAdCabinetResponseSchema(many=True), required=True)
    pagination = fields.Nested(PaginationResponseSchema, required=True)
    filters = fields.Nested(FacebookPacsNameFilterResponseSchema, required=True)


class FacebookPacsBusinessPortfolioRequestSchema(Schema):
    name = fields.String(required=True)
    isBanned = fields.Boolean(required=True)


class FacebookPacsBusinessPortfolioResponseSchema(FacebookPacsBusinessPortfolioRequestSchema):
    id = fields.Integer(required=True)
    executors = fields.Nested(FacebookPacsExecutorResponseSchema(many=True), required=True)
    adCabinets = fields.Nested(FacebookPacsAdCabinetResponseSchema(many=True), required=True)


class FacebookPacsExecutorListResponseSchema(Schema):
    content = fields.Nested(FacebookPacsExecutorResponseSchema(many=True), required=True)
    pagination = fields.Nested(PaginationResponseSchema, required=True)
    filters = fields.Nested(FacebookPacsNameFilterResponseSchema, required=True)


class FacebookPacsBusinessPortfolioListResponseSchema(Schema):
    content = fields.Nested(FacebookPacsBusinessPortfolioResponseSchema(many=True), required=True)
    pagination = fields.Nested(PaginationResponseSchema, required=True)
    filters = fields.Nested(FacebookPacsNameFilterResponseSchema, required=True)


class FacebookPacsBusinessPageRequestSchema(Schema):
    name = fields.String(required=True)
    isBanned = fields.Boolean(required=True)


class FacebookPacsBusinessPageResponseSchema(FacebookPacsBusinessPageRequestSchema):
    id = fields.Integer(required=True)


class FacebookPacsBusinessPageListResponseSchema(Schema):
    content = fields.Nested(FacebookPacsBusinessPageResponseSchema(many=True), required=True)
    pagination = fields.Nested(PaginationResponseSchema, required=True)
    filters = fields.Nested(FacebookPacsNameFilterResponseSchema, required=True)


class FacebookPacsCampaignRequestSchema(Schema):
    name = fields.String(required=True)
    costModel = fields.Enum(CostModel, required=True)
    costValue = fields.Decimal(places=2, rounding=decimal.ROUND_DOWN, required=True)
    currency = fields.Enum(Currency, required=True)
    statusMapper = fields.Dict(required=True)
    executorId = fields.Integer(required=True)
    adCabinetId = fields.Integer(required=True)
    businessPageId = fields.Integer(required=True)

    @validates_schema
    def validate_status_mapper(self, data, **kwargs):
        validate_status_mapper(data.get('statusMapper'))


class FacebookPacsCampaignResponseSchema(Schema):
    id = fields.Integer(required=True)
    name = fields.String(required=True)
    executor = fields.Nested(FacebookPacsExecutorResponseSchema, required=True)
    adCabinet = fields.Nested(FacebookPacsAdCabinetResponseSchema, required=True)
    businessPage = fields.Nested(FacebookPacsBusinessPageResponseSchema, required=True)


class FacebookPacsCampaignListResponseSchema(Schema):
    content = fields.Nested(FacebookPacsCampaignResponseSchema(many=True), required=True)
    pagination = fields.Nested(PaginationResponseSchema, required=True)


class FacebookPacsBusinessPortfolioAccessUrlRequestSchema(Schema):
    url = fields.String(required=True)
    email = fields.Email(allow_none=True, load_default=None)
    expiresAt = fields.Date(required=True)


class FacebookPacsBusinessPortfolioAccessUrlResponseSchema(FacebookPacsBusinessPortfolioAccessUrlRequestSchema):
    id = fields.Integer(required=True)


class FacebookPacsBusinessPortfolioAccessUrlListResponseSchema(Schema):
    content = fields.Nested(FacebookPacsBusinessPortfolioAccessUrlResponseSchema(many=True), required=True)
    pagination = fields.Nested(PaginationResponseSchema, required=True)
