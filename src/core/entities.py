from peewee import AutoField, BooleanField, CharField, DatabaseProxy, ForeignKeyField, IntegerField, Model

database_proxy = DatabaseProxy()


class BaseModel(Model):
    id = AutoField()

    class Meta:
        database = database_proxy
        legacy_table_names = False


class Campaign(BaseModel):
    name = CharField()


class Flow(BaseModel):
    campaign_id = ForeignKeyField(Campaign)

    order_value = IntegerField(null=False)
    is_enabled = BooleanField(default=True)
    is_deleted = BooleanField(default=False)
