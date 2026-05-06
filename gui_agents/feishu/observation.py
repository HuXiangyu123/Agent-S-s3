"""Helpers for loading fixture-backed observations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PIL import Image


def load_fixture_metadata(image_path: str | Path) -> dict[str, Any]:
    path = Path(image_path)
    metadata_path = path.with_suffix(".json")
    if not metadata_path.exists():
        return {}
    return json.loads(metadata_path.read_text(encoding="utf-8-sig"))


def normalize_observation(observation: dict[str, Any]) -> dict[str, Any]:
    metadata = observation.get("metadata")
    if isinstance(metadata, dict):
        return metadata

    image_path = observation.get("image_path")
    if image_path:
        return load_fixture_metadata(image_path)

    return {}


def get_image_size(observation: dict[str, Any]) -> tuple[int | None, int | None]:
    width = observation.get("image_width")
    height = observation.get("image_height")
    if isinstance(width, int) and isinstance(height, int):
        return width, height

    image_path = observation.get("image_path")
    if not image_path:
        return None, None

    with Image.open(image_path) as image:
        return image.size


def _extract_relative_bounds(region: dict[str, Any]) -> list[float] | None:
    bounds = region.get("relative_bounds")
    if (
        isinstance(bounds, list)
        and len(bounds) == 4
        and all(isinstance(value, (int, float)) for value in bounds)
    ):
        return [float(value) for value in bounds]
    return None


def get_region_bounds(
    observation: dict[str, Any], region_name: str
) -> list[float] | None:
    metadata = normalize_observation(observation)
    key_regions = metadata.get("key_regions", {})
    region = key_regions.get(region_name)
    if not isinstance(region, dict):
        return None
    return _extract_relative_bounds(region)


def get_named_region_bounds(
    observation: dict[str, Any],
    collection_name: str,
    item_name: str,
) -> list[float] | None:
    metadata = normalize_observation(observation)
    named_regions = metadata.get("named_regions", {})
    if not isinstance(named_regions, dict):
        return None

    collection = named_regions.get(collection_name)
    if not isinstance(collection, dict):
        return None

    region = collection.get(item_name)
    if not isinstance(region, dict):
        return None

    return _extract_relative_bounds(region)
