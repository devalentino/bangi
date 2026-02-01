import os

from wireup import create_sync_container

from peewee import MySQLDatabase
from src.auth.services import AuthenticationService
from src.core.db import database
from src.core.entities import database_proxy
from src.core.services import CampaignService, ClientService, FlowService, Ip2LocationLocator
from src.facebook_autoregs.services import AdCabinetService as FacebookAutoregsAdCabinetService
from src.facebook_autoregs.services import BusinessPageService as FacebookAutoregsBusinessPageService
from src.facebook_autoregs.services import BusinessPortfolioService as FacebookAutoregsBusinessPortfolioService
from src.facebook_autoregs.services import CampaignService as FacebookAutoregsCampaignService
from src.facebook_autoregs.services import ExecutorService as FacebookAutoregsExecutorService
from src.reports.repositories import BaseReportRepository
from src.reports.services import ReportService
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
        BaseReportRepository,
        AuthenticationService,
        CampaignService,
        ClientService,
        FlowService,
        FacebookAutoregsAdCabinetService,
        FacebookAutoregsBusinessPageService,
        FacebookAutoregsBusinessPortfolioService,
        FacebookAutoregsCampaignService,
        FacebookAutoregsExecutorService,
        Ip2LocationLocator,
        ReportService,
        TrackService,
    ],
)

database_proxy.initialize(container.get(MySQLDatabase))
