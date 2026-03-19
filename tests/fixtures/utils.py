import time
from datetime import datetime, timezone

import pytest


@pytest.fixture
def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


@pytest.fixture
def timestamp(utcnow):
    return int(time.time())


@pytest.fixture
def today(utcnow):
    return utcnow.date()
