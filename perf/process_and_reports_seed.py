#!/usr/bin/env python3

import argparse
import os
from datetime import datetime, timezone
from pathlib import Path
from pprint import pprint

from perf_seed_common import (
    create_campaign,
    ensure_empty_campaigns_table,
    ensure_safe_db_target,
    get_connection,
    print_progress,
    seed_tracker_tables,
    validate_ratio,
)

PERF_FLOW_PREFIX = 'Perf Process Flow'
PERF_REDIRECT_URL = 'https://example.com/perf-process'
PERF_LANDING_HTML = (
    '<!DOCTYPE html>\n'
    '<html lang="en">\n'
    '<head>\n'
    '  <meta charset="utf-8">\n'
    '  <title><?php echo "PERFORMANCE TEST LANDING"; ?></title>\n'
    '</head>\n'
    '<body>\n'
    '  <h1><?php echo "PERFORMANCE TEST LANDING"; ?></h1>\n'
    '  <p><?php echo "Hello, World!"; ?></p>\n'
    '</body>\n'
    '</html>\n'
)


def parse_args():
    parser = argparse.ArgumentParser(
        description='Create campaign and flow fixtures for the process performance scenario.'
    )
    parser.add_argument(
        '--action-type',
        choices=('redirect', 'render'),
        required=True,
        help='Flow action type to create for the seeded campaign.',
    )
    parser.add_argument('--clicks', type=int, default=100_000, help='How many clicks to create.')
    parser.add_argument('--lead-ratio', type=float, default=0.30, help='Fraction of clicks that also get a lead.')
    parser.add_argument(
        '--postback-ratio', type=float, default=0.15, help='Fraction of leads that also get a postback.'
    )
    parser.add_argument('--days', type=int, default=14, help='Spread records over the last N days, including today.')
    parser.add_argument('--batch-size', type=int, default=1_000, help='Insert batch size.')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for reproducible data.')
    return parser.parse_args()


def create_flow(cursor, campaign_id, action_type):
    redirect_url = PERF_REDIRECT_URL if action_type == 'redirect' else None
    payload = {
        'name': f'{PERF_FLOW_PREFIX} {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}',
        'campaign_id': campaign_id,
        'rule': None,
        'order_value': 1,
        'action_type': action_type,
        'redirect_url': redirect_url,
        'is_enabled': True,
        'is_deleted': False,
        'created_at': int(datetime.now(timezone.utc).timestamp()),
    }
    cursor.execute(
        '''
        INSERT INTO flow (
            name, campaign_id, rule, order_value, action_type, redirect_url, is_enabled, is_deleted, created_at
        )
        VALUES (
            %(name)s, %(campaign_id)s, %(rule)s, %(order_value)s, %(action_type)s, %(redirect_url)s,
            %(is_enabled)s, %(is_deleted)s, %(created_at)s
        )
        ''',
        payload,
    )
    return cursor.lastrowid, payload['name']


def create_landing(flow_id):
    base_path = os.environ.get('LANDING_PAGES_BASE_PATH')
    if not base_path:
        raise RuntimeError('LANDING_PAGES_BASE_PATH must be set for render flow seeding.')

    landing_dir = Path(base_path) / str(flow_id)
    landing_dir.mkdir(parents=True, exist_ok=True)
    index_path = landing_dir / 'index.php'
    index_path.write_text(PERF_LANDING_HTML, encoding='utf-8')
    return str(index_path)


def main():
    args = parse_args()
    validate_ratio('lead_ratio', args.lead_ratio)
    validate_ratio('postback_ratio', args.postback_ratio)
    ensure_safe_db_target()

    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            ensure_empty_campaigns_table(cursor)
            campaign = create_campaign(cursor)
            flow_id, flow_name = create_flow(cursor, campaign['id'], args.action_type)
            landing_index_path = None
            if args.action_type == 'render':
                landing_index_path = create_landing(flow_id)
        connection.commit()

        seed_tracker_tables(
            connection=connection,
            campaign=campaign,
            clicks=args.clicks,
            lead_ratio=args.lead_ratio,
            postback_ratio=args.postback_ratio,
            days=args.days,
            batch_size=args.batch_size,
            seed=args.seed,
            progress_callback=print_progress,
        )
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    pprint(
        {
            'campaign_id': campaign['id'],
            'campaign_name': campaign['name'],
            'flow_id': flow_id,
            'flow_name': flow_name,
            'action_type': args.action_type,
            'redirect_url': PERF_REDIRECT_URL if args.action_type == 'redirect' else None,
            'landing_index_path': landing_index_path,
        }
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
