import hashlib
from typing import Annotated

from peewee import fn
from wireup import Inject, injectable

from src.core.entities import Campaign
from src.core.exceptions import CampaignDoesNotExistError
from src.core.enums import SortOrder
from src.domains.entities import Domain
from src.domains.enums import DomainPurpose
from src.domains.exceptions import (
    CampaignAlreadyBoundError,
    DashboardDomainCannotAttachCampaignError,
    DomainAlreadyExistsError,
    DomainDoesNotExistError,
)


@injectable
class DomainService:
    def __init__(self, flow_id_cookie_key_length: Annotated[int, Inject(config='FLOW_ID_COOKIE_KEY_LENGTH')]):
        self.flow_id_cookie_key_length = flow_id_cookie_key_length

    def get(self, id):
        try:
            return Domain.get_by_id(id)
        except Domain.DoesNotExist as exc:
            raise DomainDoesNotExistError() from exc

    def list(self, page, page_size, sort_by, sort_order):
        order_by = getattr(Domain, sort_by)
        if sort_order == SortOrder.desc:
            order_by = order_by.desc()

        return [
            domain
            for domain in Domain.select().order_by(order_by, Domain.id.asc()).limit(page_size).offset((page - 1) * page_size)
        ]

    def count(self):
        return Domain.select(fn.count(Domain.id)).scalar()

    def create(self, hostname, purpose, is_disabled=False):
        if Domain.select(fn.count(Domain.id)).where(Domain.hostname == hostname).scalar():
            raise DomainAlreadyExistsError()

        domain = Domain(
            hostname=hostname,
            purpose=purpose.value,
            is_disabled=is_disabled,
            is_a_record_set=None,
        )
        domain.save()
        return domain

    def update(
        self,
        domain_id,
        hostname=None,
        purpose=None,
        campaign_id=None,
        is_disabled=None,
    ):
        domain = self.get(domain_id)

        if hostname is not None and hostname != domain.hostname:
            if Domain.select(fn.count(Domain.id)).where((Domain.hostname == hostname) & (Domain.id != domain.id)).scalar():
                raise DomainAlreadyExistsError()
            domain.hostname = hostname
            domain.is_a_record_set = None

        if campaign_id is None:
            domain.campaign = None
        else:
            if domain.campaign_id is not None and campaign_id != domain.campaign_id:
                self._ensure_campaign_is_available(campaign_id, domain.id)

            if purpose == DomainPurpose.dashboard:
                raise DashboardDomainCannotAttachCampaignError()

            campaign = self._get_campaign(campaign_id)
            domain.campaign = campaign

        if purpose is not None:
            if purpose == DomainPurpose.dashboard and campaign_id is not None:
                raise DashboardDomainCannotAttachCampaignError()
            domain.purpose = purpose.value

        if is_disabled is not None:
            domain.is_disabled = is_disabled

        domain.save()
        return domain

    def cookie_name(self, hostname, purpose):
        if purpose != DomainPurpose.campaign:
            return None
        return hashlib.sha256(hostname.encode()).hexdigest()[: self.flow_id_cookie_key_length]

    def _get_campaign(self, campaign_id):
        try:
            return Campaign.get_by_id(campaign_id)
        except Campaign.DoesNotExist as exc:
            raise CampaignDoesNotExistError() from exc

    def _ensure_campaign_is_available(self, campaign_id, domain_id):
        query = Domain.select(fn.count(Domain.id)).where((Domain.campaign == campaign_id) & (Domain.id != domain_id))
        if query.scalar():
            raise CampaignAlreadyBoundError()
