import decimal

from marshmallow import fields, validates_schema

from src.core.enums import CostModel, Currency
from src.core.schemas import PaginationRequestSchema, PaginationResponseSchema, Schema, validate_status_mapper


class NameFilterResponseSchema(Schema):
    partialName = fields.String(allow_none=True, required=True)


class BusinessPortfolioNestedResponseSchema(Schema):
    id = fields.Integer(required=True)
    name = fields.String(required=True)
    isBanned = fields.Boolean(required=True)


class ExecutorRequestSchema(Schema):
    name = fields.String(required=True)
    isBanned = fields.Boolean(required=True)


class ExecutorResponseSchema(ExecutorRequestSchema):
    id = fields.Integer(required=True)


class NameFilterRequestSchema(PaginationRequestSchema):
    partialName = fields.String(load_default=None)


class AdCabinetRequestSchema(Schema):
    name = fields.String(required=True)
    isBanned = fields.Boolean(required=True)


class AdCabinetResponseSchema(ExecutorRequestSchema):
    id = fields.Integer(required=True)
    businessPortfolio = fields.Nested(BusinessPortfolioNestedResponseSchema())


class AdCabinetListResponseSchema(Schema):
    content = fields.Nested(AdCabinetResponseSchema(many=True), required=True)
    pagination = fields.Nested(PaginationResponseSchema, required=True)
    filters = fields.Nested(NameFilterResponseSchema, required=True)


class BusinessPortfolioRequestSchema(Schema):
    name = fields.String(required=True)
    isBanned = fields.Boolean(required=True)


class BusinessPortfolioResponseSchema(ExecutorRequestSchema):
    id = fields.Integer(required=True)
    executors = fields.Nested(ExecutorResponseSchema(many=True), required=True)
    adCabinets = fields.Nested(AdCabinetResponseSchema(many=True), required=True)


class ExecutorListResponseSchema(Schema):
    content = fields.Nested(ExecutorResponseSchema(many=True), required=True)
    pagination = fields.Nested(PaginationResponseSchema, required=True)
    filters = fields.Nested(NameFilterResponseSchema, required=True)


class BusinessPortfolioListResponseSchema(Schema):
    content = fields.Nested(BusinessPortfolioResponseSchema(many=True), required=True)
    pagination = fields.Nested(PaginationResponseSchema, required=True)
    filters = fields.Nested(NameFilterResponseSchema, required=True)


class BusinessPageRequestSchema(Schema):
    name = fields.String(required=True)
    isBanned = fields.Boolean(required=True)


class BusinessPageResponseSchema(BusinessPageRequestSchema):
    id = fields.Integer(required=True)


class BusinessPageListResponseSchema(Schema):
    content = fields.Nested(BusinessPageResponseSchema(many=True), required=True)
    pagination = fields.Nested(PaginationResponseSchema, required=True)
    filters = fields.Nested(NameFilterResponseSchema, required=True)


class CampaignRequestSchema(Schema):
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


class CampaignResponseSchema(Schema):
    id = fields.Integer(required=True)
    name = fields.String(required=True)
    executor = fields.Nested(ExecutorResponseSchema, required=True)
    adCabinet = fields.Nested(AdCabinetResponseSchema, required=True)
    businessPage = fields.Nested(BusinessPageResponseSchema, required=True)


class CampaignListResponseSchema(Schema):
    content = fields.Nested(CampaignResponseSchema(many=True), required=True)
    pagination = fields.Nested(PaginationResponseSchema, required=True)


class BusinessPortfolioAccessUrlRequestSchema(Schema):
    url = fields.String(required=True)
    expiresAt = fields.Date(required=True)


class BusinessPortfolioAccessUrlResponseSchema(BusinessPortfolioAccessUrlRequestSchema):
    id = fields.Integer(required=True)


class BusinessPortfolioAccessUrlListResponseSchema(Schema):
    content = fields.Nested(BusinessPortfolioAccessUrlResponseSchema(many=True), required=True)
    pagination = fields.Nested(PaginationResponseSchema, required=True)
