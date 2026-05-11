from peewee import BooleanField, CharField, ForeignKeyField

from src.core.entities import Campaign, Entity


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
