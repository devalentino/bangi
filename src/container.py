import os
from typing import TypeVar

from wireup import create_sync_container

from peewee import MySQLDatabase
from src.alerts.repositories import BusinessPortfolioRepository
from src.alerts.services import AlertService
from src.auth.services import AuthenticationService
from src.core.db import database
from src.core.entities import database_proxy
from src.core.services import CampaignService, ClientService, FlowService, Ip2LocationLocator
from src.core.supervisor import WorkerContext, WorkerSupervisor
from src.facebook_pacs.services import AdCabinetService as FacebookPacsAdCabinetService
from src.facebook_pacs.services import BusinessPageService as FacebookPacsBusinessPageService
from src.facebook_pacs.services import BusinessPortfolioService as FacebookPacsBusinessPortfolioService
from src.facebook_pacs.services import CampaignService as FacebookPacsCampaignService
from src.facebook_pacs.services import ExecutorService as FacebookPacsExecutorService
from src.reports.repositories import StatisticsReportRepository
from src.reports.services import ReportHelperService, ReportService
from src.tracker.services import TrackService

T = TypeVar('T')


def _get_env(name, cast: type[T] = str, default: T | None = None) -> T | None:
    value = os.getenv(name)
    if value is None:
        return default
    return cast(value)


container = create_sync_container(
    parameters={
        'MARIADB_HOST': _get_env('MARIADB_HOST'),
        'MARIADB_PORT': _get_env('MARIADB_PORT', int),
        'MARIADB_USER': _get_env('MARIADB_USER'),
        'MARIADB_PASSWORD': _get_env('MARIADB_PASSWORD'),
        'MARIADB_DATABASE': _get_env('MARIADB_DATABASE'),
        'BASIC_AUTHENTICATION_USERNAME': _get_env('BASIC_AUTHENTICATION_USERNAME'),
        'BASIC_AUTHENTICATION_PASSWORD': _get_env('BASIC_AUTHENTICATION_PASSWORD'),
        'REPORT_GAP_SECONDS': _get_env('REPORT_GAP_SECONDS', int, 30 * 60 * 60),
        'BACKGROUND_SUPERVISOR_POLL_SECONDS': _get_env('BACKGROUND_SUPERVISOR_POLL_SECONDS', float, 1.0),
        'ACCESS_URL_EXPIRING_SOON_DAYS': _get_env('ACCESS_URL_EXPIRING_SOON_DAYS', int, 5),
        'LANDING_PAGES_BASE_PATH': _get_env('LANDING_PAGES_BASE_PATH'),
        'IP2LOCATION_DB_PATH': _get_env('IP2LOCATION_DB_PATH'),
        'LANDING_PAGE_RENDERER_BASE_URL': _get_env('LANDING_PAGE_RENDERER_BASE_URL'),
        'INTERNAL_PROCESS_BASE_URL': _get_env('INTERNAL_PROCESS_BASE_URL'),
    },
    services=[
        database,
        WorkerContext,
        WorkerSupervisor,
        BusinessPortfolioRepository,
        StatisticsReportRepository,
        AlertService,
        AuthenticationService,
        CampaignService,
        ClientService,
        FlowService,
        FacebookPacsAdCabinetService,
        FacebookPacsBusinessPageService,
        FacebookPacsBusinessPortfolioService,
        FacebookPacsCampaignService,
        FacebookPacsExecutorService,
        Ip2LocationLocator,
        ReportHelperService,
        ReportService,
        TrackService,
    ],
)

database_proxy.initialize(container.get(MySQLDatabase))
