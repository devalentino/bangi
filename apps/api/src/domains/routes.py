import humps
from flask.views import MethodView

from src.auth import auth
from src.container import container
from src.core.blueprint import Blueprint
from src.domains.schemas import (
    DomainCreateRequestSchema,
    DomainListRequestSchema,
    DomainListResponseSchema,
    DomainResponseSchema,
    DomainUpdateRequestSchema,
)
from src.domains.services import DomainService
from src.health.services import HealthService


def _validation_failed(domain):
    snapshot = container.get(HealthService).latest_nginx_validation_snapshot()
    return bool(snapshot is not None and snapshot.validation_status == 'failed' and snapshot.domain_id == domain.id)


blueprint = Blueprint('domains', __name__, description='Domains')


@blueprint.route('')
class Domains(MethodView):
    @blueprint.arguments(DomainListRequestSchema, location='query')
    @blueprint.response(200, DomainListResponseSchema)
    @auth.login_required
    def get(self, parameters_payload):
        domain_service = container.get(DomainService)
        domains = domain_service.list(
            parameters_payload['page'],
            parameters_payload['pageSize'],
            humps.decamelize(parameters_payload['sortBy'].value),
            parameters_payload['sortOrder'],
        )
        return {
            'content': [
                humps.camelize(
                    {
                        'id': domain.id,
                        'hostname': domain.hostname,
                        'purpose': domain.purpose,
                        'campaign_id': domain.campaign_id,
                        'campaign_name': None if domain.campaign_id is None else domain.campaign.name,
                        'validation_failed': False,
                        'is_a_record_set': (None if domain.is_a_record_set is None else bool(domain.is_a_record_set)),
                        'is_disabled': bool(domain.is_disabled),
                    }
                )
                for domain in domains
            ],
            'pagination': parameters_payload | {'total': domain_service.count()},
        }

    @blueprint.arguments(DomainCreateRequestSchema)
    @blueprint.response(201, DomainResponseSchema)
    @auth.login_required
    def post(self, payload):
        domain_service = container.get(DomainService)
        domain = domain_service.create(payload['hostname'], payload['purpose'], payload.get('isDisabled', False))
        return humps.camelize(
            {
                'id': domain.id,
                'hostname': domain.hostname,
                'purpose': domain.purpose,
                'campaign_id': domain.campaign_id,
                'campaign_name': None if domain.campaign_id is None else domain.campaign.name,
                'validation_failed': False,
                'is_a_record_set': None if domain.is_a_record_set is None else bool(domain.is_a_record_set),
                'is_disabled': bool(domain.is_disabled),
            }
        )


@blueprint.route('/<int:domainId>')
class Domain(MethodView):
    @blueprint.response(200, DomainResponseSchema)
    @auth.login_required
    def get(self, domainId):
        domain_service = container.get(DomainService)
        domain = domain_service.get(domainId)
        return humps.camelize(
            {
                'id': domain.id,
                'hostname': domain.hostname,
                'purpose': domain.purpose,
                'campaign_id': domain.campaign_id,
                'campaign_name': None if domain.campaign_id is None else domain.campaign.name,
                'validation_failed': _validation_failed(domain),
                'is_a_record_set': None if domain.is_a_record_set is None else bool(domain.is_a_record_set),
                'is_disabled': bool(domain.is_disabled),
            }
        )

    @blueprint.arguments(DomainUpdateRequestSchema)
    @blueprint.response(200, DomainResponseSchema)
    @auth.login_required
    def patch(self, payload, domainId):
        domain_service = container.get(DomainService)
        domain = domain_service.update(
            domainId,
            hostname=payload.get('hostname'),
            purpose=payload.get('purpose'),
            campaign_id=payload.get('campaignId'),
            is_disabled=payload.get('isDisabled'),
        )
        return humps.camelize(
            {
                'id': domain.id,
                'hostname': domain.hostname,
                'purpose': domain.purpose,
                'campaign_id': domain.campaign_id,
                'campaign_name': None if domain.campaign_id is None else domain.campaign.name,
                'validation_failed': _validation_failed(domain),
                'is_a_record_set': None if domain.is_a_record_set is None else bool(domain.is_a_record_set),
                'is_disabled': bool(domain.is_disabled),
            }
        )
