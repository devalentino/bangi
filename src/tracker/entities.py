from peewee import CharField, DecimalField, IntegerField
from src.core.entities import Entity
from src.peewee import JSONField


class TrackClick(Entity):
    click_id = CharField()
    campaign_id = IntegerField()
    parameters = JSONField()


class TrackPostback(Entity):
    click_id = CharField()
    parameters = JSONField()
    status = CharField(null=True)
    cost_value = DecimalField(null=True)
    currency = CharField(null=True)
