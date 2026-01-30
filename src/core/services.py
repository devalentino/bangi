import dataclasses
import logging
import os
import shutil
import tempfile
import zipfile
from typing import Annotated, Protocol

import httpx
import IP2Location
import rule_engine
import user_agents
from wireup import Inject, injectable, service

from peewee import fn
from src.core.entities import Campaign, Flow
from src.core.enums import FlowActionType, SortOrder
from src.core.exceptions import DoesNotExistError, LandingPageUploadError
from src.core.models import Client

logger = logging.getLogger(__name__)


@injectable
class IpLocator(Protocol):
    def get_country(self, address):
        pass


@injectable(as_type=IpLocator)
class Ip2LocationLocator:
    def __init__(self, ip2location_db_path: Annotated[str, Inject(param='IP2LOCATION_DB_PATH')]):
        self.ip2location = None
        try:
            self.ip2location = IP2Location.IP2Location(ip2location_db_path)
        except ValueError:
            logger.warning('IP2Location database is not valid')

    def get_country(self, address):
        try:
            country = self.ip2location.get_country_short(address)
        except Exception:
            logger.warning('Failed to get country by ip', extra={'address': address})
            return None

        if len(country) != 2:
            logger.warning('Failed to get country by ip', extra={'address': address})
            return None

        return country


@service
class ClientService:
    def __init__(self, ip_locator: IpLocator):
        self.ip_locator = ip_locator

    def client_info(self, user_agent, ip_address) -> Client:
        user_agent = user_agents.parse(user_agent)
        return Client(
            browser_family=user_agent.browser.family,
            device_family=user_agent.device.family,
            os_family=user_agent.os.family,
            country=self.ip_locator.get_country(ip_address),
            is_bot=user_agent.is_bot,
            is_mobile=user_agent.is_mobile,
        )


@service
class CampaignService:
    def get(self, id):
        try:
            return Campaign.get_by_id(id)
        except Campaign.DoesNotExist as exc:
            raise DoesNotExistError() from exc

    def list(self, page, page_size, sort_by, sort_order):
        order_by = getattr(Campaign, sort_by)
        if sort_order == SortOrder.desc:
            order_by = order_by.desc()

        return [c for c in Campaign.select().order_by(order_by).limit(page_size).offset((page - 1) * page_size)]

    def all(self):
        return [c for c in Campaign.select()]

    def create(self, name, cost_model, cost_value, currency, status_mapper=None):
        campaign = Campaign(
            name=name,
            cost_model=cost_model,
            cost_value=cost_value,
            currency=currency,
            status_mapper=status_mapper,
        )
        campaign.save()
        return campaign

    def update(self, campaign_id, name=None, cost_model=None, cost_value=None, currency=None, status_mapper=None):
        campaign = self.get(campaign_id)

        if name:
            campaign.name = name

        if cost_model:
            campaign.cost_model = cost_model

        if cost_value:
            campaign.cost_value = cost_value

        if currency:
            campaign.currency = currency

        if status_mapper is not None:
            campaign.status_mapper = status_mapper

        campaign.save()

        return campaign

    def count(self):
        return Campaign.select(fn.count(Campaign.id)).scalar()


@service
class FlowService:
    def __init__(
        self,
        landing_pages_base_path: Annotated[str, Inject(param='LANDING_PAGES_BASE_PATH')],
        landing_renderer_base_url: Annotated[str, Inject(param='LANDING_PAGE_RENDERER_BASE_URL')],
    ):
        self.landing_pages_base_path = landing_pages_base_path
        self.landing_renderer_base_url = landing_renderer_base_url

    def _store_landing_archive(self, flow_id, landing_archive):
        if not self.landing_pages_base_path:
            logger.error('Landing archives base path is not configured')
            raise LandingPageUploadError()

        landing_dir = os.path.join(self.landing_pages_base_path, str(flow_id))
        if os.path.exists(landing_dir):
            shutil.rmtree(landing_dir)
        os.makedirs(landing_dir, exist_ok=True)

        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
            landing_archive.save(temp_file.name)
            temp_path = temp_file.name

        try:
            with zipfile.ZipFile(temp_path) as archive:
                archive.extractall(landing_dir)
        finally:
            os.remove(temp_path)

        return landing_dir

    def _render_landing_page(self, flow_id):
        response = httpx.get(f'{self.landing_renderer_base_url}/{flow_id}')
        return response.text

    def get(self, id):
        try:
            return Flow.get_by_id(id)
        except Flow.DoesNotExist as exc:
            raise DoesNotExistError() from exc

    def list(self, page, page_size, sort_by, sort_order):
        order_by = getattr(Flow, sort_by)
        if sort_order == SortOrder.desc:
            order_by = order_by.desc()

        return [
            f
            for f in Flow.select().where(Flow.is_deleted == False).order_by(order_by).limit(page_size).offset(page - 1)
        ]

    def create(
        self,
        campaign_id,
        rule,
        order_value,
        action_type,
        redirect_url=None,
        is_enabled=True,
        landing_archive=None,
    ):
        flow = Flow(
            campaign_id=campaign_id,
            rule=rule,
            order_value=order_value,
            action_type=action_type,
            redirect_url=redirect_url,
            is_enabled=is_enabled,
        )
        flow.save()

        if action_type == FlowActionType.render:
            self._store_landing_archive(flow.id, landing_archive)

        return flow

    def update(
        self,
        flow_id,
        rule=None,
        order_value=None,
        action_type=None,
        redirect_url=None,
        is_enabled=None,
        landing_archive=None,
    ):
        flow = Flow.get_by_id(flow_id)
        if rule is not None:
            flow.rule = rule

        if order_value is not None:
            flow.order_value = order_value

        if action_type is not None:
            flow.action_type = action_type
            flow.redirect_url = redirect_url

            if action_type == FlowActionType.render:
                self._store_landing_archive(flow.id, landing_archive)

        if is_enabled is not None:
            flow.is_enabled = is_enabled

        flow.save()
        return flow

    def count(self):
        return Flow.select(fn.count(Flow.id)).where(Flow.is_deleted == False).scalar()

    def process_flows(self, campaign_id: int, client: Client):
        flows = Flow.select().where(Flow.campaign_id == campaign_id).order_by(Flow.order_value.desc())

        matched_flow = None
        for flow in flows:
            rule = rule_engine.Rule(flow.rule, context=Client.rule_engine_context())
            if rule.matches(dataclasses.asdict(client)):
                matched_flow = flow
                break

        if matched_flow is None:
            logger.warning(
                'Failed to process flows', extra={'campaign_id': campaign_id, 'flows': [f.to_dict() for f in flows]}
            )
            return None, None

        if matched_flow.action_type == FlowActionType.redirect:
            return matched_flow.action_type, matched_flow.redirect_url
        elif matched_flow.action_type == FlowActionType.render:
            return matched_flow.action_type, self._render_landing_page(matched_flow.id)

        return None, None
