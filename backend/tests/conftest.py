from pathlib import Path

import pytest
from config.celery import app as celery_app


FIXTURES = Path(__file__).parent / "fixtures"


def fixture_text(*parts: str) -> str:
    return (FIXTURES.joinpath(*parts)).read_text(encoding="utf-8")


@pytest.fixture
def eager_celery():
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True
    yield
    celery_app.conf.task_always_eager = False
    celery_app.conf.task_eager_propagates = False
