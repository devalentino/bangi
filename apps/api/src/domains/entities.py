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
