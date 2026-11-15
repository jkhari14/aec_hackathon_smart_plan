"""Distances between lot and footprint outlines, in metres, with no packages to install.

Coordinates are GeoJSON longitude and latitude. Over one city block a flat projection around the shape is
accurate to centimetres, which is far finer than the tax map and footprints agree with each other.
"""

from __future__ import annotations

import math

Point = tuple[float, float]
Segment = tuple[Point, Point]

_M_PER_DEG_LAT = 110_540.0
_M_PER_DEG_LON_AT_EQUATOR = 111_320.0


def rings(geometry: dict) -> list[list[list[float]]]:
    """Every ring of a Polygon or MultiPolygon."""
    if geometry.get("type") == "Polygon":
        return list(geometry["coordinates"])
    if geometry.get("type") == "MultiPolygon":
        return [ring for polygon in geometry["coordinates"] for ring in polygon]
    return []


def bounds(geometry: dict) -> tuple[float, float, float, float]:
    points = [p for ring in rings(geometry) for p in ring]
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    return min(xs), min(ys), max(xs), max(ys)


def _segments(geometry: dict, lat0: float, lon0: float) -> list[Segment]:
    scale = _M_PER_DEG_LON_AT_EQUATOR * math.cos(math.radians(lat0))
    out = []
    for ring in rings(geometry):
        pts = [((p[0] - lon0) * scale, (p[1] - lat0) * _M_PER_DEG_LAT) for p in ring]
        out += list(zip(pts, pts[1:]))
    return out


def _point_segment(p: Point, s: Segment) -> float:
    (x1, y1), (x2, y2) = s
    dx, dy = x2 - x1, y2 - y1
    length2 = dx * dx + dy * dy
    t = 0.0 if length2 == 0 else max(0.0, min(1.0, ((p[0] - x1) * dx + (p[1] - y1) * dy) / length2))
    return math.hypot(p[0] - (x1 + t * dx), p[1] - (y1 + t * dy))


def _cross(o: Point, a: Point, b: Point) -> float:
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def _segment_distance(a: Segment, b: Segment) -> float:
    d1, d2 = _cross(b[0], b[1], a[0]), _cross(b[0], b[1], a[1])
    d3, d4 = _cross(a[0], a[1], b[0]), _cross(a[0], a[1], b[1])
    if d1 * d2 < 0 and d3 * d4 < 0:
        return 0.0
    return min(_point_segment(a[0], b), _point_segment(a[1], b), _point_segment(b[0], a), _point_segment(b[1], a))


def near(a: dict, b: dict, metres: float) -> bool:
    """Do the outlines of two shapes come within `metres` of each other?"""
    ax0, ay0, ax1, ay1 = bounds(a)
    bx0, by0, bx1, by1 = bounds(b)
    pad_lat = metres / _M_PER_DEG_LAT
    pad_lon = metres / (_M_PER_DEG_LON_AT_EQUATOR * math.cos(math.radians(ay0)))
    if ax0 > bx1 + pad_lon or bx0 > ax1 + pad_lon or ay0 > by1 + pad_lat or by0 > ay1 + pad_lat:
        return False
    lat0, lon0 = (ay0 + ay1) / 2, (ax0 + ax1) / 2
    sa, sb = _segments(a, lat0, lon0), _segments(b, lat0, lon0)
    return any(_segment_distance(x, y) <= metres for x in sa for y in sb)


def shared_edge_m(a: dict, b: dict, metres: float = 1.0) -> float:
    """Roughly how long the stretch of `a`'s outline lying within `metres` of `b`'s is."""
    ax0, ay0, ax1, ay1 = bounds(a)
    lat0, lon0 = (ay0 + ay1) / 2, (ax0 + ax1) / 2
    sb = _segments(b, lat0, lon0)
    total = 0.0
    for (p, q) in _segments(a, lat0, lon0):
        length = math.hypot(q[0] - p[0], q[1] - p[1])
        steps = max(1, int(length // 0.5))
        close = sum(1 for i in range(steps + 1)
                    if min(_point_segment((p[0] + (q[0] - p[0]) * i / steps, p[1] + (q[1] - p[1]) * i / steps), s)
                           for s in sb) <= metres)
        total += length * close / (steps + 1)
    return total
