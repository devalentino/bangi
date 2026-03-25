#!/usr/bin/env python3

import argparse
import json
import os
import random
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID, uuid4

import pymysql
from pymysql.cursors import DictCursor


def parse_args():
    parser = argparse.ArgumentParser(description='Seed tracker data for performance testing.')
    parser.add_argument('--campaign-id', type=int, required=True, help='Existing campaign id.')
    parser.add_argument('--clicks', type=int, default=100_000, help='How many clicks to create.')
    parser.add_argument('--lead-ratio', type=float, default=0.30, help='Fraction of clicks that also get a lead.')
    parser.add_argument(
        '--postback-ratio', type=float, default=0.15, help='Fraction of leads that also get a postback.'
    )
    parser.add_argument('--days', type=int, default=14, help='Spread records over the last N days, including today.')
    parser.add_argument('--batch-size', type=int, default=1_000, help='Insert batch size.')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for reproducible data.')
    parser.add_argument(
        '--truncate',
        action='store_true',
        help='Delete existing tracker rows for the campaign before inserting new data.',
    )
    return parser.parse_args()


def validate_ratio(name, value):
    if not 0 <= value <= 1:
        raise ValueError(f'{name} must be between 0 and 1')


def now_timestamp():
    return int(datetime.now(timezone.utc).timestamp())


def timestamp_in_last_days(days):
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=max(days - 1, 0))
    delta_seconds = int((now - start).total_seconds())
    offset = random.randint(0, max(delta_seconds, 0))
    return int((start + timedelta(seconds=offset)).timestamp())


def click_parameters(iteration):
    sources = ('fb', 'tt', 'gg', 'native')
    countries = ('US', 'DE', 'FR', 'PL', 'UA')
    return {
        'source': 'k6-seed',
        'utm_source': random.choice(sources),
        'adset_name': f'adset-{iteration % 50}',
        'ad_name': f'ad-{iteration % 250}',
        'country': random.choice(countries),
        'pixel': 'perf',
    }


def lead_parameters():
    return {
        'source': 'k6-seed',
        'state': random.choice(('queued', 'new', 'pending')),
    }


def postback_payload(cost_value, currency):
    status = random.choices(('accept', 'reject', 'expect'), weights=(0.55, 0.25, 0.20), k=1)[0]
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


def json_or_value(value):
    if isinstance(value, (dict, list)):
        return json.dumps(value)
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, UUID):
        return value.bytes
    return value


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


def is_local_db_host(host):
    return host in {'localhost', '127.0.0.1', '::1', 'mariadb', 'docker.local'}


def confirm_remote_target(host):
    if not sys.stdin.isatty():
        raise RuntimeError(
            'Refusing to seed a non-local database target without an interactive terminal. '
            f'MARIADB_HOST={host!r}.'
        )

    print(f'WARNING: non-local database target detected: MARIADB_HOST={host}', file=sys.stderr)
    confirmation = input("Type 'yes' to continue: ").strip()
    if confirmation != 'yes':
        raise RuntimeError('Aborted by user.')


def ensure_safe_db_target():
    host = os.environ['MARIADB_HOST']
    if is_local_db_host(host):
        return

    confirm_remote_target(host)


def get_campaign(cursor, campaign_id):
    cursor.execute('SELECT id, cost_value, currency FROM campaign WHERE id = %(campaign_id)s', {'campaign_id': campaign_id})
    return cursor.fetchone()


def delete_existing_data(cursor, campaign_id):
    cursor.execute(
        '''
        DELETE tl
        FROM track_lead tl
        INNER JOIN track_click tc ON tc.click_id = tl.click_id
        WHERE tc.campaign_id = %(campaign_id)s
        ''',
        {'campaign_id': campaign_id},
    )
    cursor.execute(
        '''
        DELETE tp
        FROM track_postback tp
        INNER JOIN track_click tc ON tc.click_id = tp.click_id
        WHERE tc.campaign_id = %(campaign_id)s
        ''',
        {'campaign_id': campaign_id},
    )
    cursor.execute('DELETE FROM track_click WHERE campaign_id = %(campaign_id)s', {'campaign_id': campaign_id})


def insert_many(cursor, table_name, rows):
    if not rows:
        return 0

    columns = list(rows[0].keys())
    placeholders = ', '.join(['%s'] * len(columns))
    query = f'INSERT INTO {table_name} ({", ".join(columns)}) VALUES ({placeholders})'
    values = [tuple(json_or_value(row[column]) for column in columns) for row in rows]
    cursor.executemany(query, values)
    return len(rows)


def flush_rows(connection, click_rows, lead_rows, postback_rows):
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


def print_progress(clicks, leads, postbacks, done=False):
    prefix = 'Done' if done else 'Progress'
    print(f'{prefix}: clicks={clicks}, leads={leads}, postbacks={postbacks}')


def main():
    args = parse_args()
    validate_ratio('lead_ratio', args.lead_ratio)
    validate_ratio('postback_ratio', args.postback_ratio)
    random.seed(args.seed)
    ensure_safe_db_target()

    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            campaign = get_campaign(cursor, args.campaign_id)
            if campaign is None:
                print(f'Campaign {args.campaign_id} does not exist', file=sys.stderr)
                return 1

            if args.truncate:
                print(f'Removing existing tracker rows for campaign {args.campaign_id}...')
                delete_existing_data(cursor, args.campaign_id)
                connection.commit()

        click_rows = []
        lead_rows = []
        postback_rows = []

        inserted_clicks = 0
        inserted_leads = 0
        inserted_postbacks = 0

        for iteration in range(args.clicks):
            click_id = uuid4()
            created_at = timestamp_in_last_days(args.days)

            click_rows.append(
                {
                    'click_id': click_id,
                    'campaign_id': args.campaign_id,
                    'parameters': click_parameters(iteration),
                    'created_at': created_at,
                }
            )

            has_lead = random.random() < args.lead_ratio
            if has_lead:
                lead_rows.append(
                    {
                        'click_id': click_id,
                        'parameters': lead_parameters(),
                        'created_at': min(created_at + random.randint(1, 1800), now_timestamp()),
                    }
                )

            if has_lead and random.random() < args.postback_ratio:
                payload = postback_payload(campaign['cost_value'], campaign['currency'])
                postback_rows.append(
                    {
                        'click_id': click_id,
                        'parameters': payload['parameters'],
                        'status': payload['status'],
                        'cost_value': payload['cost_value'],
                        'currency': payload['currency'],
                        'created_at': min(created_at + random.randint(60, 7200), now_timestamp()),
                    }
                )

            if len(click_rows) >= args.batch_size:
                c, l, p = flush_rows(connection, click_rows, lead_rows, postback_rows)
                inserted_clicks += c
                inserted_leads += l
                inserted_postbacks += p
                print_progress(inserted_clicks, inserted_leads, inserted_postbacks)

        c, l, p = flush_rows(connection, click_rows, lead_rows, postback_rows)
        inserted_clicks += c
        inserted_leads += l
        inserted_postbacks += p
        print_progress(inserted_clicks, inserted_leads, inserted_postbacks, done=True)
        return 0
    finally:
        connection.close()


if __name__ == '__main__':
    raise SystemExit(main())
