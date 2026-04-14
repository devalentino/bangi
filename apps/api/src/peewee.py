import datetime
import json

from peewee import TextField, TimestampField


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
