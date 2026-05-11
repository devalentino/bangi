from marshmallow import ValidationError, fields, validate, validates, validates_schema

from src.core.schemas import Schema


class DiskUtilizationIngestRequestSchema(Schema):
    filesystem = fields.String(required=True)
    mountpoint = fields.String(required=True)
    total_bytes = fields.Integer(required=True, strict=True)
    used_bytes = fields.Integer(required=True, strict=True)
    available_bytes = fields.Integer(required=True, strict=True)
    used_percent = fields.Decimal(required=True, as_string=False)

    @validates('filesystem')
    def validate_filesystem(self, value, **kwargs):
        if value.strip() == '':
            raise ValidationError('filesystem cannot be blank.')

    @validates('mountpoint')
    def validate_mountpoint(self, value, **kwargs):
        if value.strip() == '':
            raise ValidationError('mountpoint cannot be blank.')

    @validates_schema
    def validate_values(self, data, **kwargs):
        total_bytes = data.get('total_bytes')
        used_bytes = data.get('used_bytes')
        available_bytes = data.get('available_bytes')
        used_percent = data.get('used_percent')

        for field_name in ('total_bytes', 'used_bytes', 'available_bytes'):
            value = data.get(field_name)
            if value is not None and value < 0:
                raise ValidationError(f'{field_name} must be greater than or equal to 0.', field_name=field_name)

        if used_percent is not None and (used_percent < 0 or used_percent > 100):
            raise ValidationError('used_percent must be between 0 and 100.', field_name='used_percent')

        if total_bytes is None:
            return

        if used_bytes is not None and used_bytes > total_bytes:
            raise ValidationError('used_bytes must be less than or equal to total_bytes.', field_name='used_bytes')

        if available_bytes is not None and available_bytes > total_bytes:
            raise ValidationError(
                'available_bytes must be less than or equal to total_bytes.',
                field_name='available_bytes',
            )


class DiskUtilizationHistoryRequestSchema(Schema):
    days = fields.Integer(load_default=30, validate=validate.Range(min=1))


class DiskUtilizationHistoryPointResponseSchema(Schema):
    date = fields.Date(required=True)
    usedPercent = fields.Float(required=True)
    usedBytes = fields.Integer(required=True)
    availableBytes = fields.Integer(required=True)


class DiskUtilizationHistorySummaryResponseSchema(Schema):
    stale = fields.Boolean(required=True)
    severity = fields.String(allow_none=True)
    filesystem = fields.String(allow_none=True)
    mountpoint = fields.String(allow_none=True)
    totalBytes = fields.Integer(allow_none=True)
    usedBytes = fields.Integer(allow_none=True)
    availableBytes = fields.Integer(allow_none=True)
    usedPercent = fields.Float(allow_none=True)
    lastReceivedAt = fields.Integer(allow_none=True)


class DiskUtilizationHistoryResponseSchema(Schema):
    summary = fields.Nested(DiskUtilizationHistorySummaryResponseSchema, required=True)
    content = fields.Nested(DiskUtilizationHistoryPointResponseSchema(many=True), required=True)


class NginxValidationSnapshotResponseSchema(Schema):
    domainId = fields.Integer(allow_none=True, required=True)
    validationStatus = fields.String(required=True)
    validationError = fields.String(allow_none=True, required=True)
    validationTimestamp = fields.Integer(required=True)
    sitesAvailableFiles = fields.List(fields.String(), required=True)
    sitesEnabledRefs = fields.List(fields.String(), required=True)


class NginxValidationResponseSchema(Schema):
    content = fields.Nested(NginxValidationSnapshotResponseSchema, allow_none=True, required=True)
