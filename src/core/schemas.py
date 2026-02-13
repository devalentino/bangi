import decimal
import logging

import rule_engine
from marshmallow import Schema as MarshmallowSchema
from marshmallow import ValidationError, fields, validates_schema

from src.core.constants import PAGINATION_DEFAULT_PAGE_SIZE
from src.core.enums import CostModel, Currency, FlowActionType, FlowSortBy, LeadStatus, SortBy, SortOrder
from src.core.models import Client

logger = logging.getLogger(__name__)

_LEAD_STATUS_VALUES = {status.value for status in LeadStatus}


def validate_status_mapper(status_mapper):
    if status_mapper is None:
        return

    if not isinstance(status_mapper, dict):
        raise ValidationError('statusMapper must be a dict.', field_name='statusMapper')

    mapping = status_mapper.get('mapping')
    if mapping is None:
        return

    if not isinstance(mapping, dict):
        raise ValidationError('statusMapper.mapping must be a dict.', field_name='statusMapper')

    invalid_values = sorted({value for value in mapping.values() if value not in _LEAD_STATUS_VALUES})
    if invalid_values:
        allowed_values = ', '.join(sorted(_LEAD_STATUS_VALUES))
        raise ValidationError(
            f'statusMapper.mapping values must be one of: {allowed_values}.',
            field_name='statusMapper',
        )


class Schema(MarshmallowSchema):
    pass


class ComaSeparatedStringsField(fields.Field):
    def _serialize(self, value, attr, obj, **kwargs):
        if value is None:
            return ''
        return ''.join(value)

    def _deserialize(self, value, attr, data, **kwargs):
        if not isinstance(value, str):
            raise ValidationError('Field must be a string.')
        return [v.strip() for v in value.split(',')]


class PaginationRequestSchema(Schema):
    page = fields.Integer(dump_default=1, load_default=1)
    pageSize = fields.Integer(dump_default=PAGINATION_DEFAULT_PAGE_SIZE, load_default=PAGINATION_DEFAULT_PAGE_SIZE)
    sortBy = fields.Enum(SortBy, dump_default=SortBy.id, load_default=SortBy.id)
    sortOrder = fields.Enum(SortOrder, dump_default=SortOrder.asc, load_default=SortOrder.asc)


class PaginationResponseSchema(PaginationRequestSchema):
    total = fields.Integer(required=True)


class CampaignCreateRequestSchema(Schema):
    name = fields.String(required=True)
    costModel = fields.Enum(CostModel, required=True)
    costValue = fields.Decimal(places=2, rounding=decimal.ROUND_DOWN, required=True)
    currency = fields.Enum(Currency, required=True)
    statusMapper = fields.Dict(required=True)

    @validates_schema
    def validate_status_mapper(self, data, **kwargs):
        validate_status_mapper(data.get('statusMapper'))


class CampaignUpdateRequestSchema(Schema):
    name = fields.String()
    costModel = fields.Enum(CostModel)
    costValue = fields.Decimal(places=2, rounding=decimal.ROUND_DOWN)
    currency = fields.Enum(Currency)
    statusMapper = fields.Dict(allow_none=True, load_default=None)

    @validates_schema
    def validate_status_mapper(self, data, **kwargs):
        validate_status_mapper(data.get('statusMapper'))


class CampaignResponseSchema(Schema):
    id = fields.Integer(required=True)
    name = fields.String(required=True)
    costModel = fields.String(required=True)
    costValue = fields.Decimal(places=2, rounding=decimal.ROUND_DOWN, required=True)
    currency = fields.String(required=True)
    statusMapper = fields.Dict(allow_none=True)
    internalProcessUrl = fields.String(allow_none=True)
    expensesDistributionParameter = fields.String(allow_none=True)


class CampaignListResponseSchema(Schema):
    content = fields.Nested(CampaignResponseSchema(many=True), required=True)
    pagination = fields.Nested(PaginationResponseSchema, required=True)


class FilterCampaignResponseSchema(Schema):
    id = fields.Integer(required=True)
    name = fields.String(required=True)


class FlowPaginationRequestSchema(Schema):
    page = fields.Integer(dump_default=1, load_default=1)
    pageSize = fields.Integer(dump_default=PAGINATION_DEFAULT_PAGE_SIZE, load_default=PAGINATION_DEFAULT_PAGE_SIZE)
    sortBy = fields.Enum(FlowSortBy, dump_default=FlowSortBy.id, load_default=FlowSortBy.id)
    sortOrder = fields.Enum(SortOrder, dump_default=SortOrder.asc, load_default=SortOrder.asc)


class FlowPaginationResponseSchema(FlowPaginationRequestSchema):
    total = fields.Integer(required=True)


class FlowUpdateRequestSchema(Schema):
    name = fields.String(required=False)
    rule = fields.String(required=True)
    actionType = fields.Enum(FlowActionType, required=True)
    redirectUrl = fields.Url(allow_none=True, load_default=None)
    isEnabled = fields.Boolean()

    @validates_schema
    def validate_action(self, data, **kwargs):
        if data.get('actionType') == FlowActionType.redirect:
            if data.get('redirectUrl') is None:
                raise ValidationError('redirectUrl is required for redirect action.', field_name='redirectUrl')
            return

    @validates_schema
    def validate_rule(self, data, **kwargs):
        rule = data.get('rule')
        if rule is None or rule == '':
            data['rule'] = None
            return
        try:
            rule_engine.Rule(rule, context=Client.rule_engine_context())
        except rule_engine.errors.SymbolResolutionError as e:
            raise ValidationError(e.message, field_name='rule')
        except rule_engine.errors.RuleSyntaxError as e:
            raise ValidationError(e.message, field_name='rule')
        except rule_engine.errors.EngineError:
            logger.warning('Failed to save rule', exc_info=True)
            raise ValidationError('rule error', field_name='rule')

    @classmethod
    def validate_render_action_type(cls, flow_payload, landing_archive):
        if flow_payload.get('actionType') == FlowActionType.render:
            if landing_archive is None:
                raise ValidationError('landingArchive is required for render action.', field_name='landingArchive')
            if not landing_archive.filename.endswith('.zip'):
                raise ValidationError('landingArchive must be a .zip file.', field_name='landingArchive')
            return


class FlowCreateRequestSchema(FlowUpdateRequestSchema):
    name = fields.String(required=True)


class FlowBulkOrderUpdateRequestSchema(Schema):
    order = fields.Dict(keys=fields.Integer(), values=fields.Integer(), required=True)


class FlowResponseSchema(Schema):
    id = fields.Integer(required=True)
    name = fields.String(required=True)
    campaignId = fields.Integer(required=True)
    campaignName = fields.String(required=True)
    orderValue = fields.Integer(required=True)
    actionType = fields.String(required=True)
    redirectUrl = fields.String(allow_none=True)
    landingPath = fields.String(allow_none=True)
    isEnabled = fields.Boolean(required=True)
    rule = fields.String(required=True, allow_none=True)


class FlowListResponseSchema(Schema):
    content = fields.Nested(FlowResponseSchema(many=True), required=True)
    pagination = fields.Nested(FlowPaginationResponseSchema, required=True)
