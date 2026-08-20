from peewee import CharField

from src.core.entities import Entity
from src.core.peewee import UTCTimestampField


class PatToken(Entity):
    name = CharField(max_length=100)
    token_hash = CharField(max_length=64, unique=True, index=True)
    token_prefix = CharField(max_length=8)
    token_suffix = CharField(max_length=4)
    revoked_at = UTCTimestampField(null=True, utc=True)
