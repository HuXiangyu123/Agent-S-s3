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


def _extract_runtime_bounds(region: dict[str, Any]) -> list[int] | None:
    bounds = region.get("bounds")
    if (
        isinstance(bounds, list)
        and len(bounds) == 4
        and all(isinstance(value, int) for value in bounds)
    ):
        return bounds
    return None


def get_runtime_region_bounds(
    observation: dict[str, Any], region_name: str
) -> list[int] | None:
    """Read runtime-only absolute bounds.

    Static fixture metadata and page descriptors are intentionally ignored here:
    persisted Feishu semantic data must not carry coordinates.
    """
    runtime_regions = observation.get("runtime_regions", {})
    if not isinstance(runtime_regions, dict):
        return None
    region = runtime_regions.get(region_name)
    if not isinstance(region, dict):
        return None
    return _extract_runtime_bounds(region)


def get_named_runtime_region_bounds(
    observation: dict[str, Any],
    collection_name: str,
    item_name: str,
) -> list[int] | None:
    """Read runtime-only absolute bounds for a named detected item."""
    named_regions = observation.get("runtime_named_regions", {})
    if not isinstance(named_regions, dict):
        return None

    collection = named_regions.get(collection_name)
    if not isinstance(collection, dict):
        return None

    region = collection.get(item_name)
    if not isinstance(region, dict):
        return None

    return _extract_runtime_bounds(region)
