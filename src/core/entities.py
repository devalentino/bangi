from decimal import Decimal

from playhouse.shortcuts import model_to_dict

from peewee import (
    AutoField,
    BooleanField,
    CharField,
    DatabaseProxy,
    DecimalField,
    ForeignKeyField,
    IntegerField,
)
from peewee import Model as PeeweeModel
from peewee import (
    TextField,
    TimestampField,
)
from src.core.enums import CostModel, Currency, FlowActionType
from src.peewee import JSONField

database_proxy = DatabaseProxy()


class Model(PeeweeModel):
    class Meta:
        database = database_proxy
        legacy_table_names = False
        primary_key = False
        evolve = False

    def to_dict(self):
        return model_to_dict(self)


class Entity(Model):
    id = AutoField(primary_key=True)
    created_at = TimestampField(null=True, utc=True)

    class Meta:
        evolve = False


class Campaign(Entity):
    name = CharField()
    cost_model = CharField(null=True, default=CostModel.cpa.value)
    cost_value = DecimalField(null=True, default=Decimal('0.00'))
    currency = CharField(null=True, default=Currency.usd.value)
    status_mapper = JSONField(null=True)


class Flow(Entity):
    campaign_id = ForeignKeyField(Campaign)
    rule = TextField(null=True)
    order_value = IntegerField(null=False)
    action_type = CharField(default=FlowActionType.redirect.value)
    redirect_url = CharField(null=True)
    is_enabled = BooleanField(default=True)
    is_deleted = BooleanField(default=False)
