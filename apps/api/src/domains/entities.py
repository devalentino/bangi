from peewee import BooleanField, CharField, ForeignKeyField, IntegerField, TextField

from src.core.entities import Campaign, Entity
from src.core.peewee import UTCTimestampField


class Domain(Entity):
    hostname = CharField(max_length=255, unique=True)
    purpose = CharField(max_length=32)
    campaign = ForeignKeyField(Campaign, null=True, unique=True)
    is_a_record_set = BooleanField(null=True)
    is_disabled = BooleanField(default=False)

    class Meta:
        table_name = 'domain'


class DomainCookie(Entity):
    domain = ForeignKeyField(Domain, on_delete='CASCADE')
    name = CharField(max_length=64)
    opaque_name = CharField(max_length=64)

    class Meta:
        table_name = 'domain_cookie'
        indexes = ((('domain', 'name'), True), (('domain', 'opaque_name'), True))


class DomainCertificate(Entity):
    domain = ForeignKeyField(Domain, on_delete='CASCADE', unique=True)
    status = CharField(max_length=32)
    ca = CharField(max_length=32)
    validation_method = CharField(max_length=32)
    certificate_path = CharField(max_length=512, null=True)
    private_key_path = CharField(max_length=512, null=True)
    issued_at = UTCTimestampField(null=True, utc=True)
    expires_at = UTCTimestampField(null=True, utc=True)
    last_attempted_at = UTCTimestampField(null=True, utc=True)
    last_issued_at = UTCTimestampField(null=True, utc=True)
    last_renewed_at = UTCTimestampField(null=True, utc=True)
    next_retry_at = UTCTimestampField(null=True, utc=True)
    failure_count = IntegerField(default=0)
    failure_reason = TextField(null=True)

    class Meta:
        table_name = 'domain_certificate'
