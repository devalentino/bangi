from peewee import CharField, DateField, DecimalField, ForeignKeyField, IntegerField
from src.core.entities import Campaign, Entity
from src.core.peewee import BinaryUUIDField, JSONField, UTCTimestampField


class Expense(Entity):
    campaign = ForeignKeyField(Campaign)
    date = DateField()
    distribution = JSONField()

    class Meta:
        indexes = ((('campaign', 'date'), True),)


class ReportLead(Entity):
    click_id = BinaryUUIDField()
    campaign_id = IntegerField()
    click_created_at = UTCTimestampField(null=True, utc=True)
    status = CharField(null=True)
    cost_value = DecimalField(max_digits=10, decimal_places=5, null=True)
    currency = CharField(null=True)

    class Meta:
        indexes = (
            (('click_id',), True),
            (('campaign_id', 'click_created_at'), False),
        )
