from peewee import TextField

from src.core.entities import Model
from src.core.peewee import BinaryUUIDField, UTCTimestampField, VectorField
from src.core.utils import utcnow

EMBEDDING_DIMENSIONS = 64


class AgentNote(Model):
    session_id = BinaryUUIDField(primary_key=True)
    note_text = TextField()
    embedding = VectorField(dimensions=EMBEDDING_DIMENSIONS)
    updated_at = UTCTimestampField(default=utcnow, utc=True)
