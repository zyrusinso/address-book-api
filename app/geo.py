"""Geographic distance helpers."""

from __future__ import annotations

from math import asin, cos, radians, sin, sqrt

EARTH_RADIUS_KM = 6371.0088


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in kilometers between two lat/lon points."""
    lat1_r, lon1_r, lat2_r, lon2_r = map(radians, (lat1, lon1, lat2, lon2))

    dlat = lat2_r - lat1_r
    dlon = lon2_r - lon1_r

    a = sin(dlat / 2) ** 2 + cos(lat1_r) * cos(lat2_r) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))

    return EARTH_RADIUS_KM * c


def bounding_box(lat: float, lon: float, radius_km: float) -> tuple[float, float, float, float]:
    """Approximate lat/lon bounding box for a center point and radius.

    Used as a cheap pre-filter in SQL before computing the exact haversine
    distance in Python, so a proximity search doesn't have to scan the whole
    table's worth of Python-side distance calculations unnecessarily.
    """
    lat_delta = radius_km / 111.0  # ~111 km per degree of latitude
    # Degrees of longitude per km shrink toward the poles; guard against
    # division by ~0 near lat = +/-90.
    lon_delta = radius_km / max(111.320 * cos(radians(lat)), 1e-6)

    min_lat = max(lat - lat_delta, -90)
    max_lat = min(lat + lat_delta, 90)
    min_lon = max(lon - lon_delta, -180)
    max_lon = min(lon + lon_delta, 180)

    return min_lat, max_lat, min_lon, max_lon
