"""
Entity resolver — turn intent entities into hex_ids + category keys.

Handles four kinds of anchor:
  - explicit hex_ids
  - lat/lng coords
  - location name (PA / landmark from intent parser)
  - "anchor hex" for a location = nearest-to-landmark hex in canonical set
"""
from typing import Optional, Tuple
import h3

from .intent.parser import SGP_LOCATIONS, CATEGORIES


def resolve_anchor_hex(entities: dict, hub) -> Optional[str]:
    """Best-effort single anchor hex from intent entities."""
    # 1. explicit hex_id
    hx = entities.get("hex_ids") or []
    if isinstance(hx, list) and hx:
        return hx[0]
    th = entities.get("target_hex")
    if th:
        return th
    ah = entities.get("anchor_hexes")
    if isinstance(ah, list) and ah:
        return ah[0]

    # 2. explicit coords → h3 cell
    coords = entities.get("coords")
    if coords:
        if isinstance(coords, list) and coords and isinstance(coords[0], (list, tuple)):
            lat, lng = coords[0]
        elif isinstance(coords, (list, tuple)) and len(coords) == 2:
            lat, lng = coords
        else:
            lat, lng = None, None
        if lat is not None:
            hid = h3.latlng_to_cell(float(lat), float(lng), 9)
            if hub.features.identity(hid)["found"]:
                return hid

    # 3. location name from rule-based extractor: list of dicts
    locs = entities.get("locations")
    if isinstance(locs, list) and locs:
        loc = locs[0]
        lat, lng = loc.get("lat"), loc.get("lng")
        if lat is not None:
            hid = h3.latlng_to_cell(float(lat), float(lng), 9)
            if hub.features.identity(hid)["found"]:
                return hid

    # 4. location name from LLM: single string
    loc_str = entities.get("location")
    if isinstance(loc_str, str):
        key = loc_str.lower().strip()
        if key in SGP_LOCATIONS:
            _, (lat, lng) = SGP_LOCATIONS[key]
            hid = h3.latlng_to_cell(lat, lng, 9)
            if hub.features.identity(hid)["found"]:
                return hid

    return None


def resolve_all_anchors(entities: dict, hub) -> list[str]:
    """Return ALL hex anchors (not just the primary) — for multi-anchor centroid queries."""
    out = []
    hx = entities.get("hex_ids") or []
    if isinstance(hx, list):
        out.extend(hx)
    ah = entities.get("anchor_hexes")
    if isinstance(ah, list):
        out.extend(ah)
    # Coords
    coords = entities.get("coords") or []
    if isinstance(coords, list):
        for c in coords:
            if isinstance(c, (list, tuple)) and len(c) == 2:
                out.append(h3.latlng_to_cell(float(c[0]), float(c[1]), 9))
    # Rule-based locations list
    locs = entities.get("locations")
    if isinstance(locs, list):
        for loc in locs:
            if isinstance(loc, dict) and "lat" in loc and "lng" in loc:
                out.append(h3.latlng_to_cell(float(loc["lat"]), float(loc["lng"]), 9))
    # LLM single location
    loc_str = entities.get("location")
    if isinstance(loc_str, str):
        key = loc_str.lower().strip()
        if key in SGP_LOCATIONS:
            _, (lat, lng) = SGP_LOCATIONS[key]
            out.append(h3.latlng_to_cell(lat, lng, 9))
    # Dedupe preserving order + keep only canonical hexes
    seen = set()
    filtered = []
    for h in out:
        if h not in seen and hub.features.identity(h)["found"]:
            seen.add(h)
            filtered.append(h)
    return filtered


def resolve_category(entities: dict) -> Optional[str]:
    """Canonical category key (e.g. 'cafe_coffee') from entities."""
    # rule-based: list
    cats = entities.get("categories")
    if isinstance(cats, list) and cats:
        return cats[0]
    # LLM: single string
    cat = entities.get("category")
    if isinstance(cat, str):
        key = cat.lower().strip()
        if key in CATEGORIES:
            return CATEGORIES[key]
        # Already canonical?
        if key.startswith("pc_cat_"):
            return key.replace("pc_cat_", "")
        return key
    return None


def resolve_k(entities: dict, default: int = 10) -> int:
    k = entities.get("k")
    if isinstance(k, int) and 1 <= k <= 500:
        return k
    return default


def resolve_brand(entities: dict) -> Optional[str]:
    brands = entities.get("brands")
    if isinstance(brands, list) and brands:
        return brands[0]
    b = entities.get("brand")
    if isinstance(b, str) and b.strip():
        return b.strip().lower()
    return None


def resolve_location_name(entities: dict) -> Optional[str]:
    locs = entities.get("locations")
    if isinstance(locs, list) and locs:
        return locs[0].get("name")
    loc = entities.get("location")
    if isinstance(loc, str):
        return loc
    return None
