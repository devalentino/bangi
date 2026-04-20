import argparse
import json
import sys

from marshmallow import ValidationError

from src.health.schemas import DiskUtilizationIngestRequestSchema


def _build_parser():
    parser = argparse.ArgumentParser(prog='python -m src.health.ingest.disk_utilization')
    parser.add_argument('--filesystem', required=True)
    parser.add_argument('--mountpoint', required=True)
    parser.add_argument('--total-bytes', required=True, type=int)
    parser.add_argument('--used-bytes', required=True, type=int)
    parser.add_argument('--available-bytes', required=True, type=int)
    parser.add_argument('--used-percent', required=True)
    return parser


def main(argv=None):
    from src.container import container
    from src.health.services import HealthService

    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        payload = DiskUtilizationIngestRequestSchema().load(
            {
                'filesystem': args.filesystem,
                'mountpoint': args.mountpoint,
                'total_bytes': args.total_bytes,
                'used_bytes': args.used_bytes,
                'available_bytes': args.available_bytes,
                'used_percent': args.used_percent,
            }
        )
    except ValidationError as exc:
        print(json.dumps({'errors': exc.messages}, sort_keys=True), file=sys.stderr)
        return 2

    container.get(HealthService).ingest_disk_utilization(**payload)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
