import json
import os
import random
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pprint import pprint
from uuid import UUID, uuid4

import pymysql
from pymysql.cursors import DictCursor

PERF_CAMPAIGN_PREFIX = 'Perf Process Campaign'
PERF_STATUS_MAPPER = {'parameter': 'state', 'mapping': {'executed': 'accept', 'failed': 'reject'}}
PERF_COST_MODEL = 'cpa'
PERF_COST_VALUE = 10.0
PERF_CURRENCY = 'usd'


def is_local_db_host(host):
    return host in {'localhost', '127.0.0.1', '::1', 'mariadb', 'docker.local'}


def confirm_remote_target(host):
    if not sys.stdin.isatty():
        raise RuntimeError(
            'Refusing to seed a non-local database target without an interactive terminal. ' f'MARIADB_HOST={host!r}.'
        )

    print(f'WARNING: non-local database target detected: MARIADB_HOST={host}', file=sys.stderr)
    confirmation = input("Type 'yes' to continue: ").strip()
    if confirmation != 'yes':
        raise RuntimeError('Aborted by user.')


def ensure_safe_db_target():
    host = os.environ['MARIADB_HOST']
    if not is_local_db_host(host):
        confirm_remote_target(host)


def count_campaigns(cursor):
    cursor.execute('SELECT COUNT(*) AS count FROM campaign')
    return cursor.fetchone()['count']


def ensure_empty_campaigns_table(cursor):
    campaign_count = count_campaigns(cursor)
    if campaign_count != 0:
        raise RuntimeError(
            f'Refusing to seed because the database already contains {campaign_count} campaign(s). '
            'Performance seed scripts must run against an empty campaigns table.'
        )


def get_connection():
    return pymysql.connect(
        host=os.environ['MARIADB_HOST'],
        port=int(os.environ['MARIADB_PORT']),
        user=os.environ['MARIADB_USER'],
        password=os.environ['MARIADB_PASSWORD'],
        database=os.environ['MARIADB_DATABASE'],
        cursorclass=DictCursor,
        autocommit=False,
    )


def create_campaign(cursor):
    payload = {
        'name': f'{PERF_CAMPAIGN_PREFIX} {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}',
        'cost_model': PERF_COST_MODEL,
        'cost_value': PERF_COST_VALUE,
        'currency': PERF_CURRENCY,
        'status_mapper': json.dumps(PERF_STATUS_MAPPER),
        'expenses_distribution_parameter': None,
        'created_at': int(datetime.now(timezone.utc).timestamp()),
    }
    cursor.execute(
        '''
        INSERT INTO campaign (
            name, cost_model, cost_value, currency, status_mapper, expenses_distribution_parameter, created_at
        )
        VALUES (
            %(name)s, %(cost_model)s, %(cost_value)s, %(currency)s, %(status_mapper)s,
            %(expenses_distribution_parameter)s, %(created_at)s
        )
        ''',
        payload,
    )
    payload['id'] = cursor.lastrowid
    return payload


def now_timestamp():
    return int(datetime.now(timezone.utc).timestamp())


def print_progress(clicks, leads, postbacks, done=False):
    prefix = 'Done' if done else 'Progress'
    print(f'{prefix}: clicks={clicks}, leads={leads}, postbacks={postbacks}')


def validate_ratio(name, value):
    if not 0 <= value <= 1:
        raise ValueError(f'{name} must be between 0 and 1')


def timestamp_in_last_days(days, random_generator):
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=max(days - 1, 0))
    delta_seconds = int((now - start).total_seconds())
    offset = random_generator.randint(0, max(delta_seconds, 0))
    return int((start + timedelta(seconds=offset)).timestamp())


def click_parameters(iteration, random_generator):
    sources = ('fb', 'tt', 'gg', 'native')
    countries = ('US', 'DE', 'FR', 'PL', 'UA')
    return {
        'source': 'k6-seed',
        'utm_source': random_generator.choice(sources),
        'adset_name': f'adset-{iteration % 50}',
        'ad_name': f'ad-{iteration % 250}',
        'country': random_generator.choice(countries),
        'pixel': 'perf',
    }


def lead_parameters(random_generator):
    return {
        'source': 'k6-seed',
        'state': random_generator.choice(('queued', 'new', 'pending')),
    }


def postback_payload(cost_value, currency, random_generator):
    status = random_generator.choices(('accept', 'reject', 'expect'), weights=(0.55, 0.25, 0.20), k=1)[0]
    payout = None
    payout_currency = None
    if status in {'accept', 'expect'}:
        payout = cost_value
        payout_currency = currency

    return {
        'parameters': {
            'source': 'k6-seed',
            'state': 'executed' if status == 'accept' else 'failed' if status == 'reject' else 'queued',
        },
        'status': status,
        'cost_value': payout,
        'currency': payout_currency,
    }


def serialize(value):
    if isinstance(value, (dict, list)):
        return json.dumps(value)
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, UUID):
        return value.bytes
    return value


def insert_many(cursor, table_name, rows):
    if not rows:
        return 0

    columns = list(rows[0].keys())
    placeholders = ', '.join(['%s'] * len(columns))
    query = f'INSERT INTO {table_name} ({", ".join(columns)}) VALUES ({placeholders})'
    values = [tuple(serialize(row[column]) for column in columns) for row in rows]
    cursor.executemany(query, values)
    return len(rows)


def flush_tracker_rows(connection, click_rows, lead_rows, postback_rows):
    inserted_clicks = inserted_leads = inserted_postbacks = 0
    with connection.cursor() as cursor:
        inserted_clicks = insert_many(cursor, 'track_click', click_rows)
        inserted_leads = insert_many(cursor, 'track_lead', lead_rows)
        inserted_postbacks = insert_many(cursor, 'track_postback', postback_rows)
    connection.commit()
    click_rows.clear()
    lead_rows.clear()
    postback_rows.clear()
    return inserted_clicks, inserted_leads, inserted_postbacks


def seed_tracker_tables(
    connection,
    campaign,
    clicks,
    lead_ratio,
    postback_ratio,
    days,
    batch_size,
    seed,
    progress_callback=None,
):
    random_generator = random.Random(seed)
    click_rows = []
    lead_rows = []
    postback_rows = []

    inserted_clicks = 0
    inserted_leads = 0
    inserted_postbacks = 0

    for iteration in range(clicks):
        click_id = uuid4()
        created_at = timestamp_in_last_days(days, random_generator)

        click_rows.append(
            {
                'click_id': click_id,
                'campaign_id': campaign['id'],
                'parameters': click_parameters(iteration, random_generator),
                'created_at': created_at,
            }
        )

        has_lead = random_generator.random() < lead_ratio
        if has_lead:
            lead_rows.append(
                {
                    'click_id': click_id,
                    'parameters': lead_parameters(random_generator),
                    'created_at': min(created_at + random_generator.randint(1, 1800), now_timestamp()),
                }
            )

        if has_lead and random_generator.random() < postback_ratio:
            payload = postback_payload(campaign['cost_value'], campaign['currency'], random_generator)
            postback_rows.append(
                {
                    'click_id': click_id,
                    'parameters': payload['parameters'],
                    'status': payload['status'],
                    'cost_value': payload['cost_value'],
                    'currency': payload['currency'],
                    'created_at': min(created_at + random_generator.randint(60, 7200), now_timestamp()),
                }
            )

        if len(click_rows) >= batch_size:
            clicks_count, leads_count, postbacks_count = flush_tracker_rows(
                connection, click_rows, lead_rows, postback_rows
            )
            inserted_clicks += clicks_count
            inserted_leads += leads_count
            inserted_postbacks += postbacks_count
            if progress_callback is not None:
                progress_callback(inserted_clicks, inserted_leads, inserted_postbacks, False)

    clicks_count, leads_count, postbacks_count = flush_tracker_rows(connection, click_rows, lead_rows, postback_rows)
    inserted_clicks += clicks_count
    inserted_leads += leads_count
    inserted_postbacks += postbacks_count
    if progress_callback is not None:
        progress_callback(inserted_clicks, inserted_leads, inserted_postbacks, True)

    pprint({'clicks': inserted_clicks, 'leads': inserted_leads, 'postbacks': inserted_postbacks})
    return inserted_clicks, inserted_leads, inserted_postbacks
