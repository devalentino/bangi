from peewee import CharField, DecimalField, IntegerField, UUIDField
from src.core.entities import Entity
from src.peewee import JSONField


class TrackClick(Entity):
    click_id = UUIDField()
    campaign_id = IntegerField()
    parameters = JSONField()

    class Meta:
        table_settings = ('ENGINE=Aria', 'TRANSACTIONAL=0')
        indexes = ((('click_id',), False),)


class TrackPostback(Entity):
    click_id = UUIDField()
    parameters = JSONField()
    status = CharField(null=True)
    cost_value = DecimalField(null=True)
    currency = CharField(null=True)

    class Meta:
        table_settings = ('ENGINE=Aria', 'TRANSACTIONAL=0')


class TrackLead(Entity):
    click_id = UUIDField()
    parameters = JSONField()

    class Meta:
        table_settings = ('ENGINE=Aria', 'TRANSACTIONAL=0')
