import hashlib
import time
from datetime import datetime, timezone
from uuid import UUID

import pytest


def click_uuid(value):
    return UUID(f'00000000-0000-0000-0000-{value:012d}')


def cookie_name(hostname, length=6):
    return hashlib.sha256(hostname.encode()).hexdigest()[:length]


@pytest.fixture
def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


@pytest.fixture
def timestamp(utcnow):
    return int(time.time())


@pytest.fixture
def today(utcnow):
    return utcnow.date()
