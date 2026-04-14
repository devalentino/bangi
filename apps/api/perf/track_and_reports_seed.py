#!/usr/bin/env python3

import argparse
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


def parse_args():
    parser = argparse.ArgumentParser(description='Seed tracker data for performance testing.')
    parser.add_argument('--clicks', type=int, default=100_000, help='How many clicks to create.')
    parser.add_argument('--lead-ratio', type=float, default=0.30, help='Fraction of clicks that also get a lead.')
    parser.add_argument(
        '--postback-ratio', type=float, default=0.15, help='Fraction of leads that also get a postback.'
    )
    parser.add_argument('--days', type=int, default=14, help='Spread records over the last N days, including today.')
    parser.add_argument('--batch-size', type=int, default=1_000, help='Insert batch size.')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for reproducible data.')
    return parser.parse_args()


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
        pprint({'campaign_id': campaign['id'], 'campaign_name': campaign['name']})
        return 0
    finally:
        connection.close()


if __name__ == '__main__':
    raise SystemExit(main())
