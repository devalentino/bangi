from peewee import TextField

from src.core.entities import Model
from src.core.peewee import BinaryUUIDField, JSONField, UTCTimestampField, VectorField
from src.core.utils import utcnow

EMBEDDING_DIMENSIONS = 64


class AgentNote(Model):
    session_id = BinaryUUIDField(primary_key=True)
    note_text = TextField()
    campaign_ids = JSONField(default=list)
    embedding = VectorField(dimensions=EMBEDDING_DIMENSIONS)
    updated_at = UTCTimestampField(default=utcnow, utc=True)
