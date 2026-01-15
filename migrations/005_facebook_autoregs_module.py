"""Peewee migrations -- 005_facebook_autoregs_module.py.

Some examples (model - class or model name)::

    > Model = migrator.orm['table_name']            # Return model in current state by name
    > Model = migrator.ModelClass                   # Return model in current state by name

    > migrator.sql(sql)                             # Run custom SQL
    > migrator.run(func, *args, **kwargs)           # Run python function with the given args
    > migrator.create_model(Model)                  # Create a model (could be used as decorator)
    > migrator.remove_model(model, cascade=True)    # Remove a model
    > migrator.add_fields(model, **fields)          # Add fields to a model
    > migrator.change_fields(model, **fields)       # Change fields
    > migrator.remove_fields(model, *field_names, cascade=True)
    > migrator.rename_field(model, old_field_name, new_field_name)
    > migrator.rename_table(model, new_table_name)
    > migrator.add_index(model, *col_names, unique=False)
    > migrator.add_not_null(model, *field_names)
    > migrator.add_default(model, field_name, default)
    > migrator.add_constraint(model, name, sql)
    > migrator.drop_index(model, *col_names)
    > migrator.drop_not_null(model, *field_names)
    > migrator.drop_constraints(model, *constraints)

"""

from contextlib import suppress

import decimal
import peewee as pw
from peewee_migrate import Migrator


with suppress(ImportError):
    import playhouse.postgres_ext as pw_pext


def migrate(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your migrations here."""

    migrator.change_fields('campaign', cost_value=pw.DecimalField(auto_round=False, decimal_places=5, default=decimal.Decimal('0'), max_digits=10, null=True, rounding=decimal.ROUND_HALF_EVEN))

    @migrator.create_model
    class BusinessPortfolio(pw.Model):
        id = pw.AutoField()
        created_at = pw.TimestampField(null=True)
        name = pw.CharField(max_length=255)
        is_banned = pw.BooleanField()

        class Meta:
            table_name = "facebook_autoregs_business_portfolio"

    @migrator.create_model
    class AdCabinet(pw.Model):
        id = pw.AutoField()
        created_at = pw.TimestampField(null=True)
        name = pw.CharField(max_length=255)
        is_banned = pw.BooleanField()
        business_portfolio = pw.ForeignKeyField(column_name='business_portfolio_id', field='id', model=migrator.orm['facebook_autoregs_business_portfolio'], null=True)

        class Meta:
            table_name = "facebook_autoregs_ad_cabinet"

    @migrator.create_model
    class BusinessPage(pw.Model):
        id = pw.AutoField()
        created_at = pw.TimestampField(null=True)
        name = pw.CharField(max_length=255)
        is_banned = pw.BooleanField()

        class Meta:
            table_name = "facebook_autoregs_business_page"

    @migrator.create_model
    class BusinessPortfolioAccessUrl(pw.Model):
        id = pw.AutoField()
        created_at = pw.TimestampField(null=True)
        business_portfolio = pw.ForeignKeyField(column_name='business_portfolio_id', field='id', model=migrator.orm['facebook_autoregs_business_portfolio'], null=True)
        url = pw.CharField(max_length=255)
        expires_at = pw.TimestampField(null=True)

        class Meta:
            table_name = "facebook_autoregs_business_portfolio_access_url"

    @migrator.create_model
    class Executor(pw.Model):
        id = pw.AutoField()
        created_at = pw.TimestampField(null=True)
        name = pw.CharField(max_length=255)
        is_banned = pw.BooleanField()

        class Meta:
            table_name = "facebook_autoregs_executor"

    @migrator.create_model
    class BusinessPortfolioExecutorThrough(pw.Model):
        id = pw.AutoField()
        businessportfolio = pw.ForeignKeyField(column_name='businessportfolio_id', field='id', model=migrator.orm['facebook_autoregs_business_portfolio'])
        executor = pw.ForeignKeyField(column_name='executor_id', field='id', model=migrator.orm['facebook_autoregs_executor'])

        class Meta:
            table_name = "facebook_autoregs_business_portfolio2executor"
            indexes = [(('businessportfolio', 'executor'), True)]

    @migrator.create_model
    class Campaign(pw.Model):
        id = pw.AutoField()
        created_at = pw.TimestampField(null=True)
        core_campaign = pw.ForeignKeyField(column_name='core_campaign_id', field='id', model=migrator.orm['campaign'])
        ad_cabinet = pw.ForeignKeyField(column_name='ad_cabinet_id', field='id', model=migrator.orm['facebook_autoregs_ad_cabinet'])
        executor = pw.ForeignKeyField(column_name='executor_id', field='id', model=migrator.orm['facebook_autoregs_executor'])
        business_page = pw.ForeignKeyField(column_name='business_page_id', field='id', model=migrator.orm['facebook_autoregs_business_page'])

        class Meta:
            table_name = "facebook_autoregs_ad_campaign"

    @migrator.create_model
    class Entity(pw.Model):
        id = pw.AutoField()
        created_at = pw.TimestampField(null=True)

        class Meta:
            table_name = "entity"

    @migrator.create_model
    class Model(pw.Model):

        class Meta:
            table_name = "model"

    migrator.remove_model('base_model')


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your rollback migrations here."""

    migrator.change_fields('campaign', cost_value=pw.DecimalField(auto_round=False, decimal_places=5, default=decimal.Decimal('0'), max_digits=10, null=True, rounding=decimal.ROUND_DOWN))

    @migrator.create_model
    class BaseModel(pw.Model):
        id = pw.AutoField()
        created_at = pw.TimestampField(null=True)

        class Meta:
            table_name = "base_model"

    migrator.remove_model('model')

    migrator.remove_model('entity')

    migrator.remove_model('facebook_autoregs_ad_campaign')

    migrator.remove_model('facebook_autoregs_business_portfolio2executor')

    migrator.remove_model('facebook_autoregs_executor')

    migrator.remove_model('facebook_autoregs_business_portfolio_access_url')

    migrator.remove_model('facebook_autoregs_business_page')

    migrator.remove_model('facebook_autoregs_ad_cabinet')

    migrator.remove_model('facebook_autoregs_business_portfolio')
