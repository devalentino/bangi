from marshmallow import ValidationError, fields, validate, validates

from src.core.schemas import Schema


class PatTokenCreateRequestSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(max=100))

    @validates('name')
    def validate_name(self, value, **kwargs):
        if value.strip() == '':
            raise ValidationError('name cannot be blank.')


class PatTokenCreateResponseSchema(Schema):
    token = fields.String(required=True)
    name = fields.String(required=True)


class PatTokenResponseSchema(Schema):
    id = fields.Integer(required=True)
    name = fields.String(required=True)
    createdAt = fields.Integer(required=True)
    revokedAt = fields.Integer(allow_none=True, required=True)
    tokenPrefix = fields.String(required=True)
    tokenSuffix = fields.String(required=True)


class PatTokenListResponseSchema(Schema):
    content = fields.Nested(PatTokenResponseSchema(many=True), required=True)
