import humps
from flask.views import MethodView

from src.auth import auth
from src.container import container
from src.core.blueprint import Blueprint
from src.domains.exceptions import DomainCertificateDoesNotExistError
from src.domains.schemas import (
    DomainCertificateResponseSchema,
    DomainCreateRequestSchema,
    DomainListRequestSchema,
    DomainListResponseSchema,
    DomainResponseSchema,
    DomainUpdateRequestSchema,
)
from src.domains.services import CertificateService, DomainService

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
            'content': [humps.camelize(domain) for domain in domains],
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
                'is_a_record_set': None if domain.is_a_record_set is None else bool(domain.is_a_record_set),
                'is_disabled': bool(domain.is_disabled),
                'certificate_status': None,
            }
        )


@blueprint.route('/<int:domainId>')
class Domain(MethodView):
    @blueprint.response(200, DomainResponseSchema)
    @auth.login_required
    def get(self, domainId):
        domain_service = container.get(DomainService)
        certificate_service = container.get(CertificateService)
        domain = domain_service.get(domainId)

        try:
            certificate_status = certificate_service.get(domain.id).status
        except DomainCertificateDoesNotExistError:
            certificate_status = None

        return humps.camelize(
            {
                'id': domain.id,
                'hostname': domain.hostname,
                'purpose': domain.purpose,
                'campaign_id': domain.campaign_id,
                'campaign_name': None if domain.campaign_id is None else domain.campaign.name,
                'is_a_record_set': None if domain.is_a_record_set is None else bool(domain.is_a_record_set),
                'is_disabled': bool(domain.is_disabled),
                'certificate_status': certificate_status,
            }
        )

    @blueprint.arguments(DomainUpdateRequestSchema)
    @blueprint.response(200, DomainResponseSchema)
    @auth.login_required
    def patch(self, payload, domainId):
        domain_service = container.get(DomainService)
        certificate_service = container.get(CertificateService)

        domain = domain_service.update(
            domainId,
            hostname=payload.get('hostname'),
            purpose=payload.get('purpose'),
            campaign_id=payload.get('campaignId'),
            is_disabled=payload.get('isDisabled'),
        )

        try:
            certificate_status = certificate_service.get(domain.id).status
        except DomainCertificateDoesNotExistError:
            certificate_status = None

        return humps.camelize(
            {
                'id': domain.id,
                'hostname': domain.hostname,
                'purpose': domain.purpose,
                'campaign_id': domain.campaign_id,
                'campaign_name': None if domain.campaign_id is None else domain.campaign.name,
                'is_a_record_set': None if domain.is_a_record_set is None else bool(domain.is_a_record_set),
                'is_disabled': bool(domain.is_disabled),
                'certificate_status': certificate_status,
            }
        )


@blueprint.route('/<int:domainId>/certificate')
class DomainCertificate(MethodView):
    @blueprint.response(200, DomainCertificateResponseSchema)
    @auth.login_required
    def get(self, domainId):
        certificate_service = container.get(CertificateService)

        certificate = certificate_service.get(domainId)
        return humps.camelize(
            {
                'status': certificate.status,
                'ca': certificate.ca,
                'validation_method': certificate.validation_method,
                'expires_at': None if certificate.expires_at is None else int(certificate.expires_at.timestamp()),
                'last_attempted_at': (
                    None if certificate.last_attempted_at is None else int(certificate.last_attempted_at.timestamp())
                ),
                'last_issued_at': (
                    None if certificate.last_issued_at is None else int(certificate.last_issued_at.timestamp())
                ),
                'last_renewed_at': (
                    None if certificate.last_renewed_at is None else int(certificate.last_renewed_at.timestamp())
                ),
                'next_retry_at': (
                    None if certificate.next_retry_at is None else int(certificate.next_retry_at.timestamp())
                ),
                'failure_reason': certificate.failure_reason,
            }
        )
