from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import geopandas as gpd
from geopy.geocoders import Nominatim
from shapely.geometry import Point

from core.schema import GeoPayload

EMPTY_GEOJSON: Dict[str, Any] = {"type": "FeatureCollection", "features": []}


def _load_parcel_geojson(parcels_geojson_path: str) -> Dict[str, Any]:
    """Load a parcel GeoJSON file, returning an empty collection if the file is missing or blank."""
    path = Path(parcels_geojson_path)
    if not path.exists() or path.stat().st_size == 0:
        return EMPTY_GEOJSON.copy()

    try:
        raw_text = path.read_text(encoding="utf-8").strip()
    except OSError:
        return EMPTY_GEOJSON.copy()

    if not raw_text:
        return EMPTY_GEOJSON.copy()

    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError:
        return EMPTY_GEOJSON.copy()

    if isinstance(payload, dict):
        if payload.get("features") is None:
            return EMPTY_GEOJSON.copy()
        return payload

    return EMPTY_GEOJSON.copy()


def compute_impact_zone(
    address: str,
    parcels_geojson_path: str,
    radius_meters: float = 300.0,
    user_agent: str = "poleazy_agent",
) -> GeoPayload:
    """Geocode a target address, build a radius buffer, and measure affected parcels in the parcel layer."""
    geolocator = Nominatim(user_agent=user_agent, timeout=10)
    location = geolocator.geocode(address)
    if location is None:
        raise ValueError(f"Unable to geocode address: {address}")

    point = Point(location.longitude, location.latitude)
    meters_to_degrees = radius_meters / 111_320.0
    buffer_poly = point.buffer(meters_to_degrees)

    parcel_payload = _load_parcel_geojson(parcels_geojson_path)
    if not parcel_payload.get("features"):
        affected_geojson = EMPTY_GEOJSON.copy()
        affected_parcels_count = 0
    else:
        try:
            parcels_gdf = gpd.GeoDataFrame.from_features(parcel_payload["features"], crs="EPSG:4326")
        except Exception:
            parcels_gdf = gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")

        if parcels_gdf.empty or "geometry" not in parcels_gdf.columns:
            affected_geojson = EMPTY_GEOJSON.copy()
            affected_parcels_count = 0
        else:
            affected = parcels_gdf[parcels_gdf.intersects(buffer_poly)].copy()
            affected_geojson = json.loads(affected.to_json()) if not affected.empty else EMPTY_GEOJSON.copy()
            affected_parcels_count = int(len(affected))

    return GeoPayload(
        target_address=address,
        latitude=float(location.latitude),
        longitude=float(location.longitude),
        buffer_meters=float(radius_meters),
        affected_parcels_count=affected_parcels_count,
        geojson_impact_layer=affected_geojson,
    )
