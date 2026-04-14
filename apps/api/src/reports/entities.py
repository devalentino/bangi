from peewee import DateField, ForeignKeyField
from src.core.entities import Campaign, Entity
from src.peewee import JSONField


class Expense(Entity):
    campaign = ForeignKeyField(Campaign)
    date = DateField()
    distribution = JSONField()

    class Meta:
        indexes = ((('campaign', 'date'), True),)
