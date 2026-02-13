import os

from wireup import create_sync_container

from peewee import MySQLDatabase
from src.auth.services import AuthenticationService
from src.core.db import database
from src.core.entities import database_proxy
from src.core.services import CampaignService, ClientService, FlowService, Ip2LocationLocator
from src.facebook_pacs.services import AdCabinetService as FacebookPacsAdCabinetService
from src.facebook_pacs.services import BusinessPageService as FacebookPacsBusinessPageService
from src.facebook_pacs.services import BusinessPortfolioService as FacebookPacsBusinessPortfolioService
from src.facebook_pacs.services import CampaignService as FacebookPacsCampaignService
from src.facebook_pacs.services import ExecutorService as FacebookPacsExecutorService
from src.reports.repositories import StatisticsReportRepository
from src.reports.services import ReportHelperService, ReportService
from src.tracker.services import TrackService

container = create_sync_container(
    parameters={
        'MARIADB_HOST': os.getenv('MARIADB_HOST'),
        'MARIADB_PORT': os.getenv('MARIADB_PORT'),
        'MARIADB_USER': os.getenv('MARIADB_USER'),
        'MARIADB_PASSWORD': os.getenv('MARIADB_PASSWORD'),
        'MARIADB_DATABASE': os.getenv('MARIADB_DATABASE'),
        'BASIC_AUTHENTICATION_USERNAME': os.getenv('BASIC_AUTHENTICATION_USERNAME'),
        'BASIC_AUTHENTICATION_PASSWORD': os.getenv('BASIC_AUTHENTICATION_PASSWORD'),
        'REPORT_GAP_SECONDS': os.getenv('REPORT_GAP_SECONDS', 30 * 60 * 60),
        'LANDING_PAGES_BASE_PATH': os.getenv('LANDING_PAGES_BASE_PATH'),
        'IP2LOCATION_DB_PATH': os.getenv('IP2LOCATION_DB_PATH'),
        'LANDING_PAGE_RENDERER_BASE_URL': os.getenv('LANDING_PAGE_RENDERER_BASE_URL'),
        'INTERNAL_PROCESS_BASE_URL': os.getenv('INTERNAL_PROCESS_BASE_URL'),
    },
    services=[
        database,
        StatisticsReportRepository,
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
