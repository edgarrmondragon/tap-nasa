"""REST client handling, including NASAStream base class."""

from __future__ import annotations

import dataclasses
import typing as t
from datetime import date, datetime, timedelta, timezone

from singer_sdk import RESTStream
from singer_sdk import typing as th
from singer_sdk.authenticators import APIKeyAuthenticator
from singer_sdk.pagination import BaseAPIPaginator

if t.TYPE_CHECKING:
    from singer_sdk.helpers import types

DATE_FORMAT = "%Y-%m-%d"


@dataclasses.dataclass
class DateRange:
    """Date range class."""

    start: date
    interval: timedelta
    max_date: date

    @property
    def end_date(self) -> date:
        """The end date of the range."""
        return min(self.start + self.interval, self.max_date)

    def increase(self) -> DateRange:
        """Increase the date range.

        Returns:
            The increased date range.
        """
        return DateRange(
            self.start + self.interval + timedelta(days=1),
            self.interval,
            self.max_date,
        )

    def is_valid(self) -> bool:
        """Check if the date range is not past the max date.

        Returns:
            True if the date range is valid.
        """
        return self.start <= self.max_date


class DateRangePaginator(BaseAPIPaginator[DateRange]):
    """Date range paginator."""

    def __init__(self, start_value: DateRange) -> None:
        """Initialize the paginator.

        Args:
            start_value: The start value.
        """
        super().__init__(start_value)

    def get_next(self, response) -> DateRange | None:  # type: ignore[no-untyped-def]  # noqa: ANN001, ARG002
        """Get the next value.

        Args:
            response: The response.

        Returns:
            The next value.
        """
        new = self.current_value.increase()

        return new if new.is_valid() else None


class NASAStream(RESTStream[DateRange]):
    """NASA APOD stream class."""

    url_base = "https://api.nasa.gov/planetary"
    records_jsonpath = "$[*]"
    next_page_token_jsonpath = "$.next_page"  # noqa: S105

    name = "apod"
    path = "/apod"
    primary_keys = ("date",)
    replication_key = "date"

    schema = th.PropertiesList(
        th.Property(
            "date",
            th.DateTimeType,
            description="The date of the APOD image",
        ),
        th.Property(
            "title",
            th.StringType,
            description="The title of the APOD image",
        ),
        th.Property(
            "explanation",
            th.StringType,
            description="Explanation of the APOD image",
        ),
        th.Property(
            "url",
            th.StringType,
            description="URL of the APOD image",
        ),
        th.Property(
            "hdurl",
            th.StringType,
            description="HD URL of the APOD image",
        ),
        th.Property(
            "media_type",
            th.StringType,
            description="Media type of the APOD image",
        ),
        th.Property(
            "service_version",
            th.StringType,
            description="Service version of the APOD image",
        ),
        th.Property(
            "copyright",
            th.StringType,
            description="Copyright of the APOD image",
        ),
    ).to_dict()

    @property
    def authenticator(self) -> APIKeyAuthenticator:
        """Get an authenticator object.

        Returns:
            The authenticator instance for this REST stream.
        """
        return APIKeyAuthenticator.create_for_stream(
            self,
            key="api_key",
            value=self.config["api_key"],
            location="params",
        )

    @property
    def http_headers(self) -> dict[str, str]:
        """Return the http headers needed.

        Returns:
            A dictionary of HTTP headers.
        """
        return {"User-Agent": f"{self.tap_name}/{self._tap.plugin_version}"}

    def get_new_paginator(self) -> DateRangePaginator:
        """Get a new paginator."""
        start_dt = self.get_starting_timestamp(context=self.context)

        if start_dt is None:
            msg = "A start date is required"
            raise RuntimeError(msg)

        start_date = start_dt.date()

        return DateRangePaginator(
            start_value=DateRange(
                start=start_date,
                interval=timedelta(days=100),
                max_date=datetime.now(timezone.utc).date(),
            )
        )

    def get_url_params(
        self,
        context: types.Context | None,
        next_page_token: DateRange | None,
    ) -> dict[str, t.Any] | str:
        """Get URL query parameters.

        Args:
            context: Stream sync context.
            next_page_token: Next offset.

        Returns:
            Mapping of URL query parameters.
        """
        if next_page_token:
            return {
                "start_date": next_page_token.start.strftime(DATE_FORMAT),
                "end_date": next_page_token.end_date.strftime(DATE_FORMAT),
            }

        return super().get_url_params(context, next_page_token)
