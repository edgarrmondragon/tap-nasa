"""Tests standard tap features using the built-in SDK tests library."""

from __future__ import annotations

import datetime
import typing as t

from singer_sdk.testing import SuiteConfig, get_tap_test_class

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
