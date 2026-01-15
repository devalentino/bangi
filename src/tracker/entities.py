from peewee import IntegerField, UUIDField
from src.core.entities import Entity
from src.peewee import JSONField


class TrackClick(Entity):
    click_id = UUIDField()
    campaign_id = IntegerField()
    parameters = JSONField()


class TrackPostback(Entity):
    click_id = UUIDField()
    parameters = JSONField()
