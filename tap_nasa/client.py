"""REST client handling, including NASAStream base class."""

from __future__ import annotations

import dataclasses
import datetime
import typing as t

from singer_sdk import RESTStream
from singer_sdk import typing as th
from singer_sdk.authenticators import APIKeyAuthenticator
from singer_sdk.pagination import BaseAPIPaginator

DATE_FORMAT = "%Y-%m-%d"


@dataclasses.dataclass
class DateRange:
    """Date range class."""

    start: datetime.date
    end: datetime.date | None = None


class DateRangePaginator(BaseAPIPaginator[DateRange]):
    """Date range paginator."""

    def __init__(self, start_value: DateRange) -> None:
        """Initialize the paginator.

        Args:
            start_value: The start value.
        """
        super().__init__(start_value)
        self.interval = datetime.timedelta(days=100)
        self.max_date = datetime.datetime.now(datetime.timezone.utc).date()

        if self.current_value.end is None:
            self.current_value.end = self.increase(self.current_value.start)

    def increase(self, value: datetime.date) -> datetime.date:
        """Increase the value.

        Args:
            value: The value.

        Returns:
            The increased value.
        """
        return min(value + self.interval, self.max_date)

    def get_next(self, response) -> DateRange | None:  # noqa: ANN001, ARG002
        """Get the next value.

        Args:
            response: The response.

        Returns:
            The next value.
        """
        start = self.current_value.end + datetime.timedelta(days=1)
        end = self.increase(start)

        if start > self.max_date:
            return None

        return DateRange(start=start, end=end)


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

    def get_new_paginator(self) -> BaseAPIPaginator:
        """Get a new paginator."""
        start_dt = self.get_starting_timestamp(context=None)

        if start_dt is None:
            msg = "A start date is required"
            raise RuntimeError(msg)

        start_date = start_dt.date()

        return DateRangePaginator(start_value=DateRange(start=start_date))

    def get_url_params(
        self,
        context: dict[str, t.Any] | None,
        next_page_token: DateRange | None,
    ) -> dict[str, t.Any]:
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
                "end_date": next_page_token.end.strftime(DATE_FORMAT),
            }

        return super().get_url_params(context, next_page_token)
