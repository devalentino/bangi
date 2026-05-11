import re

from marshmallow import ValidationError, fields, pre_load

from src.core.schemas import PaginationRequestSchema, Schema
from src.domains.enums import DomainPurpose, DomainSortBy

_HOSTNAME_LABEL_PATTERN = re.compile(r'^(?!-)[a-z0-9-]{1,63}(?<!-)$')


def validate_hostname(hostname):
    if not isinstance(hostname, str) or hostname == '':
        raise ValidationError('hostname cannot be blank.', field_name='hostname')

    if len(hostname) > 253:
        raise ValidationError('hostname must be 253 characters or less.', field_name='hostname')

    labels = hostname.split('.')
    if len(labels) < 2:
        raise ValidationError('hostname must contain a valid domain and top-level domain.', field_name='hostname')

    if any(label == '' for label in labels):
        raise ValidationError('hostname is invalid.', field_name='hostname')

    if not all(_HOSTNAME_LABEL_PATTERN.fullmatch(label) for label in labels):
        raise ValidationError('hostname is invalid.', field_name='hostname')

    if not any(character.isalpha() for character in labels[-1]):
        raise ValidationError('hostname is invalid.', field_name='hostname')


class DomainListRequestSchema(PaginationRequestSchema):
    sortBy = fields.Enum(DomainSortBy, dump_default=DomainSortBy.id, load_default=DomainSortBy.id)


class DomainPaginationResponseSchema(DomainListRequestSchema):
    total = fields.Integer(required=True)


class DomainUpsertRequestSchema(Schema):
    hostname = fields.String(required=True, validate=validate_hostname)

    @pre_load
    def normalize_hostname(self, data, **kwargs):
        hostname = data.get('hostname')
        if isinstance(hostname, str):
            data['hostname'] = hostname.strip().rstrip('.').lower()
        return data


class DomainCreateRequestSchema(DomainUpsertRequestSchema):
    purpose = fields.Enum(DomainPurpose, by_value=True, required=True)
    isDisabled = fields.Boolean(load_default=False)


class DomainUpdateRequestSchema(DomainUpsertRequestSchema):
    hostname = fields.String(validate=validate_hostname)
    purpose = fields.Enum(DomainPurpose, by_value=True)
    campaignId = fields.Integer(allow_none=True, load_default=None)
    isDisabled = fields.Boolean()


class DomainResponseSchema(Schema):
    id = fields.Integer(required=True)
    hostname = fields.String(required=True)
    purpose = fields.String(required=True)
    campaignId = fields.Integer(allow_none=True)
    isARecordSet = fields.Boolean(allow_none=True)
    isDisabled = fields.Boolean(required=True)


class DomainListResponseSchema(Schema):
    content = fields.Nested(DomainResponseSchema(many=True), required=True)
    pagination = fields.Nested(DomainPaginationResponseSchema, required=True)
