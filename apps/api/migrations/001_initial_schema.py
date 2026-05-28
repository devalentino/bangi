"""Peewee migrations -- 001_initial_schema.py.

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
    class BusinessPortfolio(pw.Model):
        id = pw.AutoField()
        created_at = pw.TimestampField()
        name = pw.CharField(max_length=255)
        is_banned = pw.BooleanField()

        class Meta:
            table_name = "facebook_pacs_business_portfolio"

    @migrator.create_model
    class AdCabinet(pw.Model):
        id = pw.AutoField()
        created_at = pw.TimestampField()
        name = pw.CharField(max_length=255)
        is_banned = pw.BooleanField()
        business_portfolio = pw.ForeignKeyField(column_name='business_portfolio_id', field='id', model=migrator.orm['facebook_pacs_business_portfolio'], null=True)

        class Meta:
            table_name = "facebook_pacs_ad_cabinet"

    @migrator.create_model
    class BusinessPage(pw.Model):
        id = pw.AutoField()
        created_at = pw.TimestampField()
        name = pw.CharField(max_length=255)
        is_banned = pw.BooleanField()

        class Meta:
            table_name = "facebook_pacs_business_page"

    @migrator.create_model
    class BusinessPortfolioAccessUrl(pw.Model):
        id = pw.AutoField()
        created_at = pw.TimestampField()
        business_portfolio = pw.ForeignKeyField(column_name='business_portfolio_id', field='id', model=migrator.orm['facebook_pacs_business_portfolio'])
        url = pw.CharField(max_length=255)
        email = pw.CharField(max_length=255, null=True)
        expires_at = pw.TimestampField()

        class Meta:
            table_name = "facebook_pacs_business_portfolio_access_url"

    @migrator.create_model
    class Campaign(pw.Model):
        id = pw.AutoField()
        created_at = pw.TimestampField()
        name = pw.CharField(max_length=255)
        cost_model = pw.CharField(default='cpa', max_length=255)
        cost_value = pw.DecimalField(auto_round=False, decimal_places=5, default=Decimal('0'), max_digits=10, rounding=ROUND_HALF_EVEN)
        currency = pw.CharField(default='usd', max_length=255)
        status_mapper = pw.TextField(null=True)
        expenses_distribution_parameter = pw.CharField(max_length=255, null=True)
        default_flow_id = pw.IntegerField(null=True)

        class Meta:
            table_name = "campaign"

    @migrator.create_model
    class Executor(pw.Model):
        id = pw.AutoField()
        created_at = pw.TimestampField()
        name = pw.CharField(max_length=255)
        is_banned = pw.BooleanField()

        class Meta:
            table_name = "facebook_pacs_executor"

    @migrator.create_model
    class Campaign(pw.Model):
        id = pw.AutoField()
        created_at = pw.TimestampField()
        core_campaign = pw.ForeignKeyField(column_name='core_campaign_id', field='id', model=migrator.orm['campaign'])
        ad_cabinet = pw.ForeignKeyField(column_name='ad_cabinet_id', field='id', model=migrator.orm['facebook_pacs_ad_cabinet'])
        executor = pw.ForeignKeyField(column_name='executor_id', field='id', model=migrator.orm['facebook_pacs_executor'])
        business_page = pw.ForeignKeyField(column_name='business_page_id', field='id', model=migrator.orm['facebook_pacs_business_page'])

        class Meta:
            table_name = "facebook_pacs_ad_campaign"

    @migrator.create_model
    class DiskUtilization(pw.Model):
        id = pw.AutoField()
        created_at = pw.TimestampField()
        filesystem = pw.CharField(max_length=255)
        mountpoint = pw.CharField(max_length=255)
        total_bytes = pw.BigIntegerField()
        used_bytes = pw.BigIntegerField()
        available_bytes = pw.BigIntegerField()
        used_percent = pw.DecimalField(auto_round=True, decimal_places=2, max_digits=5, rounding=ROUND_HALF_EVEN)

        class Meta:
            table_name = "health_disk_utilization"

    @migrator.create_model
    class Domain(pw.Model):
        id = pw.AutoField()
        created_at = pw.TimestampField()
        hostname = pw.CharField(max_length=255, unique=True)
        purpose = pw.CharField(max_length=32)
        campaign = pw.ForeignKeyField(column_name='campaign_id', field='id', model=migrator.orm['campaign'], null=True, unique=True)
        is_a_record_set = pw.BooleanField(null=True)
        is_disabled = pw.BooleanField(default=False)

        class Meta:
            table_name = "domain"

    @migrator.create_model
    class DomainCertificate(pw.Model):
        id = pw.AutoField()
        created_at = pw.TimestampField()
        domain = pw.ForeignKeyField(column_name='domain_id', field='id', model=migrator.orm['domain'], on_delete='CASCADE', unique=True)
        status = pw.CharField(max_length=32)
        ca = pw.CharField(max_length=32)
        validation_method = pw.CharField(max_length=32)
        certificate_path = pw.CharField(max_length=512, null=True)
        private_key_path = pw.CharField(max_length=512, null=True)
        issued_at = pw.TimestampField(null=True)
        expires_at = pw.TimestampField(null=True)
        last_attempted_at = pw.TimestampField(null=True)
        last_issued_at = pw.TimestampField(null=True)
        last_renewed_at = pw.TimestampField(null=True)
        next_retry_at = pw.TimestampField(null=True)
        failure_count = pw.IntegerField(default=0)
        failure_reason = pw.TextField(null=True)

        class Meta:
            table_name = "domain_certificate"

    @migrator.create_model
    class DomainCookie(pw.Model):
        id = pw.AutoField()
        created_at = pw.TimestampField()
        domain = pw.ForeignKeyField(column_name='domain_id', field='id', model=migrator.orm['domain'], on_delete='CASCADE')
        name = pw.CharField(max_length=64)
        opaque_name = pw.CharField(max_length=64)
        encryption_key = pw.CharField(max_length=64, null=True)

        class Meta:
            table_name = "domain_cookie"
            indexes = [(('domain', 'name'), True), (('domain', 'opaque_name'), True)]

    @migrator.create_model
    class Expense(pw.Model):
        id = pw.AutoField()
        created_at = pw.TimestampField()
        campaign = pw.ForeignKeyField(column_name='campaign_id', field='id', model=migrator.orm['campaign'])
        date = pw.DateField()
        distribution = pw.TextField()

        class Meta:
            table_name = "expense"
            indexes = [(('campaign', 'date'), True)]

    @migrator.create_model
    class Flow(pw.Model):
        id = pw.AutoField()
        created_at = pw.TimestampField()
        name = pw.CharField(max_length=255)
        campaign = pw.ForeignKeyField(column_name='campaign_id', field='id', model=migrator.orm['campaign'])
        rule = pw.TextField(null=True)
        order_value = pw.IntegerField()
        action_type = pw.CharField(default='redirect', max_length=255)
        redirect_url = pw.CharField(max_length=255, null=True)
        is_enabled = pw.BooleanField(default=True)
        is_deleted = pw.BooleanField(default=False)
        show_once_per_visitor = pw.BooleanField(default=False)

        class Meta:
            table_name = "flow"

    @migrator.create_model
    class NginxValidationSnapshot(pw.Model):
        id = pw.AutoField()
        created_at = pw.TimestampField()
        domain_id = pw.IntegerField(null=True)
        validation_status = pw.CharField(max_length=16)
        validation_error = pw.TextField(null=True)
        sites_available_files = pw.TextField()
        sites_enabled_refs = pw.TextField()

        class Meta:
            table_name = "health_nginx_validation_snapshot"

    @migrator.create_model
    class ReportLead(pw.Model):
        id = pw.AutoField()
        created_at = pw.TimestampField()
        click_id = pw.Field()
        campaign_id = pw.IntegerField()
        click_created_at = pw.TimestampField()
        status = pw.CharField(max_length=255, null=True)
        cost_value = pw.DecimalField(auto_round=False, decimal_places=5, max_digits=10, null=True, rounding=ROUND_HALF_EVEN)
        currency = pw.CharField(max_length=255, null=True)

        class Meta:
            table_name = "report_lead"
            indexes = [(('click_id',), True), (('campaign_id', 'click_created_at'), False)]

    @migrator.create_model
    class TrackClick(pw.Model):
        id = pw.AutoField()
        created_at = pw.TimestampField()
        click_id = pw.Field()
        campaign_id = pw.IntegerField()
        parameters = pw.TextField()

        class Meta:
            table_name = "track_click"
            indexes = [(('click_id',), False), (('campaign_id', 'created_at', 'click_id'), False)]

    @migrator.create_model
    class TrackDiscard(pw.Model):
        id = pw.AutoField()
        created_at = pw.TimestampField()
        click_id = pw.Field()
        campaign_id = pw.IntegerField()
        country = pw.CharField(max_length=2, null=True)
        browser_family = pw.CharField(max_length=255, null=True)
        os_family = pw.CharField(max_length=255, null=True)
        device_family = pw.CharField(max_length=255, null=True)
        is_mobile = pw.BooleanField()
        is_bot = pw.BooleanField()

        class Meta:
            table_name = "track_discard"
            indexes = [(('campaign_id', 'created_at'), False), (('created_at',), False)]

    @migrator.create_model
    class TrackLead(pw.Model):
        id = pw.AutoField()
        created_at = pw.TimestampField()
        click_id = pw.Field()
        parameters = pw.TextField()

        class Meta:
            table_name = "track_lead"

    @migrator.create_model
    class TrackPostback(pw.Model):
        id = pw.AutoField()
        created_at = pw.TimestampField()
        click_id = pw.Field()
        parameters = pw.TextField()
        status = pw.CharField(max_length=255, null=True)
        cost_value = pw.DecimalField(auto_round=False, decimal_places=5, max_digits=10, null=True, rounding=ROUND_HALF_EVEN)
        currency = pw.CharField(max_length=255, null=True)

        class Meta:
            table_name = "track_postback"
            indexes = [(('click_id', 'id'), False)]


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your rollback migrations here."""
    
    migrator.remove_model('track_postback')

    migrator.remove_model('track_lead')

    migrator.remove_model('track_discard')

    migrator.remove_model('track_click')

    migrator.remove_model('report_lead')

    migrator.remove_model('health_nginx_validation_snapshot')

    migrator.remove_model('flow')

    migrator.remove_model('expense')

    migrator.remove_model('domain_cookie')

    migrator.remove_model('domain_certificate')

    migrator.remove_model('domain')

    migrator.remove_model('health_disk_utilization')

    migrator.remove_model('facebook_pacs_ad_campaign')

    migrator.remove_model('facebook_pacs_executor')

    migrator.remove_model('campaign')

    migrator.remove_model('facebook_pacs_business_portfolio_access_url')

    migrator.remove_model('facebook_pacs_business_page')

    migrator.remove_model('facebook_pacs_ad_cabinet')

    migrator.remove_model('facebook_pacs_business_portfolio')
