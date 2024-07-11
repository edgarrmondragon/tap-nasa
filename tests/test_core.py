"""Tests standard tap features using the built-in SDK tests library."""

from __future__ import annotations

import datetime
import typing as t

from singer_sdk.testing import SuiteConfig, get_tap_test_class

from tap_nasa.client import DateRange, DateRangePaginator
from tap_nasa.tap import TapNASA


def today() -> datetime.date:  # noqa: D103
    return datetime.datetime.now(datetime.timezone.utc).date()


SAMPLE_CONFIG: dict[str, t.Any] = {
    # 7 days ago
    "start_date": (today() - datetime.timedelta(days=7)).isoformat(),
}

TestTapNASA = get_tap_test_class(
    TapNASA,
    config=SAMPLE_CONFIG,
    suite_config=SuiteConfig(
        max_records_limit=10,
    ),
)


def test_date_range_pagination() -> None:
    """Test date range pagination."""
    start_date = datetime.date(2021, 1, 1)
    interval = datetime.timedelta(days=10)
    max_date = datetime.date(2021, 1, 25)

    response = object()

    paginator = DateRangePaginator(
        start_value=DateRange(
            start=start_date,
            interval=interval,
            max_date=max_date,
        )
    )
    assert paginator.current_value.start == datetime.date(2021, 1, 1)
    assert paginator.current_value.end_date == datetime.date(2021, 1, 11)

    paginator.advance(response)
    assert paginator.current_value.start == datetime.date(2021, 1, 12)
    assert paginator.current_value.end_date == datetime.date(2021, 1, 22)

    paginator.advance(response)
    assert paginator.current_value.start == datetime.date(2021, 1, 23)
    assert paginator.current_value.end_date == datetime.date(2021, 1, 25)

    paginator.advance(response)
    assert paginator.finished
