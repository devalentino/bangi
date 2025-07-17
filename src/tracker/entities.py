from peewee import IntegerField, UUIDField
from src.core.entities import BaseModel
from src.peewee import JSONField


class TrackClick(BaseModel):
    click_id = UUIDField()
    campaign_id = IntegerField()
    parameters = JSONField()
