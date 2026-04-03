from peewee import CharField, DecimalField, IntegerField
from src.core.entities import Entity
from src.core.peewee import BinaryUUIDField, JSONField


class TrackClick(Entity):
    click_id = BinaryUUIDField()
    campaign_id = IntegerField()
    parameters = JSONField()

    class Meta:
        table_settings = ('ENGINE=Aria', 'TRANSACTIONAL=0')
        indexes = ((('click_id',), False),)


class TrackPostback(Entity):
    click_id = BinaryUUIDField()
    parameters = JSONField()
    status = CharField(null=True)
    cost_value = DecimalField(null=True)
    currency = CharField(null=True)

    class Meta:
        table_settings = ('ENGINE=Aria', 'TRANSACTIONAL=0')


class TrackLead(Entity):
    click_id = BinaryUUIDField()
    parameters = JSONField()

    class Meta:
        table_settings = ('ENGINE=Aria', 'TRANSACTIONAL=0')
