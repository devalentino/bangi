from flask.views import MethodView
from peewee import MySQLDatabase

from src.auth import auth
from src.container import container
from src.core.blueprint import Blueprint
from src.health.schemas import DiskUtilizationHistoryRequestSchema, DiskUtilizationHistoryResponseSchema
from src.health.services import HealthService

blueprint = Blueprint('health', __name__, description='Health')


@blueprint.route('')
class Health(MethodView):

    @blueprint.response(200)
    def get(self):
        db_connection = container.get(MySQLDatabase)

        if db_connection.is_connection_usable():
            return {'healthy': True}
        else:
            return {'healthy': False}, 503


@blueprint.route('/disk-utilization/history')
class DiskUtilizationHistory(MethodView):
    @blueprint.arguments(DiskUtilizationHistoryRequestSchema, location='query')
    @blueprint.response(200, DiskUtilizationHistoryResponseSchema)
    @auth.login_required
    def get(self, params):
        summary, snapshots = container.get(HealthService).disk_utilization_history(days=params['days'])
        return {
            'summary': {
                'stale': summary.stale,
                'severity': summary.severity,
                'filesystem': summary.filesystem,
                'mountpoint': summary.mountpoint,
                'totalBytes': summary.total_bytes,
                'usedBytes': summary.used_bytes,
                'availableBytes': summary.available_bytes,
                'usedPercent': summary.used_percent,
                'lastReceivedAt': summary.last_received_at,
            },
            'content': [
                {
                    'createdAt': int(snapshot.created_at.timestamp()),
                    'usedPercent': float(snapshot.used_percent),
                    'usedBytes': snapshot.used_bytes,
                    'availableBytes': snapshot.available_bytes,
                }
                for snapshot in snapshots
            ],
        }
