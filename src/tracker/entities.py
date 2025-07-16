from peewee import CharField, UUIDField, IntegerField

from src.core.entities import BaseModel


class TrackClick(BaseModel):
    click_id = UUIDField()
    campaign_id = IntegerField()
    campaign_name = CharField()
    adset_name = CharField()
    ad_name = CharField()
    pixel = CharField()
