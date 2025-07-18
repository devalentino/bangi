"""Peewee migrations -- 001_initial_migration.py.

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

import peewee as pw
from peewee_migrate import Migrator


with suppress(ImportError):
    import playhouse.postgres_ext as pw_pext


def migrate(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your migrations here."""
    
    @migrator.create_model
    class BaseModel(pw.Model):
        id = pw.AutoField()

        class Meta:
            table_name = "base_model"

    @migrator.create_model
    class Campaign(pw.Model):
        id = pw.AutoField()
        name = pw.CharField(max_length=255)

        class Meta:
            table_name = "campaign"

    @migrator.create_model
    class Flow(pw.Model):
        id = pw.AutoField()
        campaign_id = pw.ForeignKeyField(column_name='campaign_id', field='id', model=migrator.orm['campaign'])
        order_value = pw.IntegerField()
        is_enabled = pw.BooleanField(default=True)
        is_deleted = pw.BooleanField(default=False)

        class Meta:
            table_name = "flow"

    @migrator.create_model
    class TrackClick(pw.Model):
        id = pw.AutoField()
        click_id = pw.UUIDField()
        campaign_id = pw.IntegerField()
        parameters = pw.TextField()

        class Meta:
            table_name = "track_click"


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your rollback migrations here."""
    
    migrator.remove_model('track_click')

    migrator.remove_model('flow')

    migrator.remove_model('campaign')

    migrator.remove_model('base_model')
