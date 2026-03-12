#!/usr/bin/env python3
"""Pull Indie Pop Meta Ad Library creatives into a Notion-ready CSV."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import os
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import requests

GRAPH_API_VERSION = "v20.0"
AD_ARCHIVE_ENDPOINT = f"https://graph.facebook.com/{GRAPH_API_VERSION}/ads_archive"

DEFAULT_FIELDS = [
    "ad_creation_time",
    "ad_delivery_start_time",
    "ad_delivery_stop_time",
    "ad_creative_bodies",
    "ad_creative_link_captions",
    "ad_creative_link_titles",
    "ad_creative_link_descriptions",
    "ad_snapshot_url",
    "page_id",
    "page_name",
    "publisher_platforms",
    "impressions_lower_bound",
    "impressions_upper_bound",
]

EU_COUNTRIES = [
    "AT",
    "BE",
    "BG",
    "HR",
    "CY",
    "CZ",
    "DK",
    "EE",
    "FI",
    "FR",
    "DE",
    "GR",
    "HU",
    "IE",
    "IT",
    "LV",
    "LT",
    "LU",
    "MT",
    "NL",
    "PL",
    "PT",
    "RO",
    "SK",
    "SI",
    "ES",
    "SE",
]


def last_month_date_range(reference: Optional[dt.date] = None) -> tuple[str, str]:
    """Return ISO date strings covering the previous calendar month."""
    today = reference or dt.date.today()
    first_of_this_month = dt.date(today.year, today.month, 1)
    last_day_last_month = first_of_this_month - dt.timedelta(days=1)
    first_day_last_month = dt.date(last_day_last_month.year, last_day_last_month.month, 1)
    return first_day_last_month.isoformat(), last_day_last_month.isoformat()


def coerce_int(value: Optional[str]) -> Optional[int]:
    """Convert numeric strings to ints (Meta returns strings for bounds)."""
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def fetch_ads(
    access_token: str,
    search_terms: str,
    countries: Iterable[str],
    date_min: str,
    date_max: str,
    limit: int = 100,
    extra_params: Optional[Dict[str, str]] = None,
) -> List[Dict]:
    """Page through the Ad Library and collect all matches."""
    params: Dict[str, str] = {
        "search_type": "KEYWORD_UNORDERED",
        "search_terms": search_terms,
        "ad_reached_countries": ",".join(sorted(countries)),
        "ad_delivery_date_min": date_min,
        "ad_delivery_date_max": date_max,
        "fields": ",".join(DEFAULT_FIELDS),
        "limit": str(limit),
    }
    if extra_params:
        params.update(extra_params)

    results: List[Dict] = []
    next_page: Optional[str] = AD_ARCHIVE_ENDPOINT

    while next_page:
        response = requests.get(
            next_page,
            params=params if next_page == AD_ARCHIVE_ENDPOINT else None,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=60,
        )
        response.raise_for_status()
        payload = response.json()
        batch = payload.get("data", [])
        results.extend(batch)
        paging = payload.get("paging", {})
        next_page = paging.get("next")
        params = None  # Subsequent requests already include query params in paging URL.

    return results


def filter_by_views(records: Iterable[Dict], min_views: int) -> List[Dict]:
    """Filter ads whose reported impression upper bound meets the threshold."""
    filtered: List[Dict] = []
    for record in records:
        upper = coerce_int(record.get("impressions_upper_bound"))
        lower = coerce_int(record.get("impressions_lower_bound"))
        estimated = upper or lower or 0
        if estimated >= min_views:
            record["_estimated_views"] = estimated
            filtered.append(record)
    return filtered


def write_notion_csv(records: Iterable[Dict], output_path: Path) -> None:
    """Save the ads into a CSV file that Notion can import as a database."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "Ad ID",
        "Page Name",
        "Creative Body",
        "Link Title",
        "Link Caption",
        "Platforms",
        "Start Date",
        "End Date",
        "Estimated Views",
        "Snapshot URL",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for item in records:
            writer.writerow(
                {
                    "Ad ID": item.get("id"),
                    "Page Name": item.get("page_name"),
                    "Creative Body": " ".join(item.get("ad_creative_bodies") or []),
                    "Link Title": " ".join(item.get("ad_creative_link_titles") or []),
                    "Link Caption": " ".join(item.get("ad_creative_link_captions") or []),
                    "Platforms": ", ".join(item.get("publisher_platforms") or []),
                    "Start Date": item.get("ad_delivery_start_time"),
                    "End Date": item.get("ad_delivery_stop_time"),
                    "Estimated Views": item.get("_estimated_views"),
                    "Snapshot URL": item.get("ad_snapshot_url"),
                }
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch Indie Pop ads from Meta Ad Library and export to Notion-ready CSV."
    )
    parser.add_argument(
        "--search-term",
        default="indie pop",
        help="Keyword to search within the Ad Library (default: %(default)s)",
    )
    parser.add_argument(
        "--countries",
        default=",".join(EU_COUNTRIES),
        help="Comma separated ISO-2 country codes (default: all EU members).",
    )
    parser.add_argument(
        "--min-views",
        type=int,
        default=10_000,
        help="Minimum impression upper bound to keep an ad (default: %(default)s).",
    )
    parser.add_argument(
        "--since",
        help="Start date (YYYY-MM-DD). Defaults to first day of previous month.",
    )
    parser.add_argument(
        "--until",
        help="End date (YYYY-MM-DD). Defaults to last day of previous month.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Page size for the API (default: %(default)s).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/meta_indie_pop_ads.csv"),
        help="Destination CSV file for Notion import.",
    )
    parser.add_argument(
        "--access-token",
        help="Meta Ad Library system user token. Falls back to META_AD_LIBRARY_TOKEN env var.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    since, until = args.since, args.until
    if not (since and until):
        since, until = last_month_date_range()
    access_token = args.access_token or os.getenv("META_AD_LIBRARY_TOKEN")
    if not access_token:
        raise SystemExit(
            "Missing Meta Ad Library access token. Provide --access-token or set META_AD_LIBRARY_TOKEN."
        )
    countries = [code.strip().upper() for code in args.countries.split(",") if code.strip()]

    ads = fetch_ads(
        access_token=access_token,
        search_terms=args.search_term,
        countries=countries,
        date_min=since,
        date_max=until,
        limit=args.limit,
    )
    filtered_ads = filter_by_views(ads, args.min_views)
    write_notion_csv(filtered_ads, args.output)

    print(
        f"Exported {len(filtered_ads)} Indie Pop ads from {since} to {until} "
        f"for {', '.join(countries)} into {args.output}"
    )


if __name__ == "__main__":
    main()
