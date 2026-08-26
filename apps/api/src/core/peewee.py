import datetime
import json
import uuid

import numpy as np
from peewee import SQL, Field, TextField, TimestampField


class JSONField(TextField):
    def db_value(self, value):
        return json.dumps(value)

    def python_value(self, value):
        if value is not None:
            return json.loads(value)


class UTCTimestampField(TimestampField):
    def python_value(self, value):
        dt = super().python_value(value)
        if dt is not None and dt.tzinfo is None:
            return dt.replace(tzinfo=datetime.timezone.utc)
        return dt


class BinaryUUIDField(Field):
    field_type = 'BINARY(16)'

    def db_value(self, value):
        if value is None:
            return None
        if isinstance(value, bytes):
            return value
        if isinstance(value, uuid.UUID):
            return value.bytes
        return uuid.UUID(str(value)).bytes

    def python_value(self, value):
        if value is None or isinstance(value, uuid.UUID):
            return value
        if isinstance(value, (bytes, bytearray)):
            return uuid.UUID(bytes=bytes(value))
        return uuid.UUID(str(value))


class VectorField(Field):
    field_type = 'VECTOR'

    def __init__(self, dimensions: int, *args, **kwargs):
        self.dimensions = dimensions
        super().__init__(*args, **kwargs)

    def db_value(self, value):
        if value is None:
            return None
        return np.asarray(value, dtype=np.float32).tobytes()

    def python_value(self, value):
        if value is None:
            return None
        return np.frombuffer(value, dtype=np.float32).tolist()

    def ddl_datatype(self, ctx):
        return SQL(f'VECTOR({self.dimensions})')
