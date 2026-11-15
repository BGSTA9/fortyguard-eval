"""
FortyGuard Temperature API - quick evaluation script.

What it does (3 heatmap requests, about 12,700 credits in total):
  1. 100 m heatmap over central Phoenix -> temperature at 3 test points.
  2. 20 m heatmap over a small box at Encanto Park -> real tile size and local variation.
  3. 100 m heatmap over the same small box -> compare with the 20 m result.
Then it pulls the same hour from Open-Meteo (independent reference) for the 3 points.

Run:
  export FORTYGUARD_API_KEY='...'      (Windows PowerShell: $env:FORTYGUARD_API_KEY='...')
  pip install requests
  python fortyguard_eval.py
"""
import json
import math
import os
import statistics
import sys
import time

import requests

API = "https://api.fortyguard.com/v1"
KEY = os.environ.get("FORTYGUARD_API_KEY")

# ---- Settings you can change -------------------------------------------------
DATE = "2025-07-15"   # a hot summer afternoon gives a stronger signal than November
TIME = sys.argv[1] if len(sys.argv) > 1 else "15:00"  # e.g. python3 fortyguard_eval.py 22:00
UTC_OFFSET_HOURS = -7  # Phoenix is UTC-7 all year

POINTS = {
    "Downtown":     (33.4484, -112.0740),
    "Encanto Park": (33.4741, -112.0890),
    "Sky Harbor":   (33.4343, -112.0116),
}
# (west, south, east, north)
BIG_BOX = (-112.1000, 33.4250, -112.0000, 33.4850)    # about 24 square miles
SMALL_BOX = (-112.0930, 33.4700, -112.0850, 33.4780)  # about 750 m x 890 m at the park
TRANSECT_LAT = 33.4741                                # west-to-east line through the park
# ------------------------------------------------------------------------------


def box_to_aoi(box):
    w, s, e, n = box
    ring = [[w, s], [e, s], [e, n], [w, n], [w, s]]
    return {"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {},
         "geometry": {"type": "Polygon", "coordinates": [ring]}}]}


def submit_heatmap(box, granularity):
    payload = {"polygon_aoi": box_to_aoi(box),
               "date_time": {"start_date": DATE, "start_time": TIME, "filter_type": 1},
               "granularity": granularity}
    t0 = time.time()
    r = requests.post(f"{API}/heatmap", json=payload, timeout=60,
                      headers={"api-key": KEY, "Content-Type": "application/json"})
    print(f"  submit: HTTP {r.status_code} in {time.time() - t0:.1f}s")
    if r.status_code != 200:
        print("  body:", r.text[:500])
        return None
    return r.json()["data"]["activity_id"]


def wait_for(activity_id, max_minutes=10):
    t0 = time.time()
    while time.time() - t0 < max_minutes * 60:
        r = requests.get(f"{API}/status/{activity_id}", headers={"api-key": KEY}, timeout=120)
        if r.status_code == 404:           # documented: can happen right after submission
            time.sleep(5)
            continue
        if r.status_code != 200:
            print(f"  status: HTTP {r.status_code}", r.text[:300])
            return None
        data = r.json().get("data", {})
        status = str(data.get("status", "")).lower()
        if status in ("completed", "succeeded"):
            print(f"  completed after {time.time() - t0:.0f}s")
            return data.get("result", {})
        if status in ("failed", "error"):
            print(f"  FAILED (activity {activity_id}):", json.dumps(data)[:400])
            return None
        time.sleep(5)
    print("  timed out waiting for the result")
    return None


def decode(obj):
    """The docs say stored maps may need a second JSON decode."""
    for _ in range(2):
        if isinstance(obj, str):
            obj = json.loads(obj)
    return obj


def find_temp_key(features):
    props = features[0].get("properties", {})
    numeric = [k for k, v in props.items() if isinstance(v, (int, float)) and not isinstance(v, bool)]
    for k in numeric:
        if "temp" in k.lower():
            return k
    return numeric[0] if numeric else None


def tile_info(feature):
    """Return (centre_lat, centre_lon, width_m, height_m) of one tile."""
    geom = feature["geometry"]
    if geom["type"] == "Point":
        lon, lat = geom["coordinates"][:2]
        return lat, lon, None, None
    ring = geom["coordinates"][0]
    if geom["type"] == "MultiPolygon":
        ring = ring[0]
    lons = [p[0] for p in ring]
    lats = [p[1] for p in ring]
    lat_c = (min(lats) + max(lats)) / 2
    lon_c = (min(lons) + max(lons)) / 2
    width = (max(lons) - min(lons)) * 111320 * math.cos(math.radians(lat_c))
    height = (max(lats) - min(lats)) * 110540
    return lat_c, lon_c, width, height


def dist_m(lat1, lon1, lat2, lon2):
    dx = (lon2 - lon1) * 111320 * math.cos(math.radians(lat1))
    dy = (lat2 - lat1) * 110540
    return math.hypot(dx, dy)


def analyse(label, result):
    """Print a summary and return a list of (lat, lon, value) tiles."""
    if not result:
        return []
    with open(f"result_{label}_{TIME.replace(':', '')}.json", "w") as f:
        json.dump(result, f)
    map_data = decode(result.get("map_data"))
    stats = decode(result.get("stats_data"))
    features = (map_data or {}).get("features", [])
    if not features:
        print("  no tiles in map_data; top-level keys:", list(result.keys()))
        return []
    print("  first tile properties:", json.dumps(features[0].get("properties", {}))[:300])
    key = find_temp_key(features)
    if key is None:
        print("  could not find a numeric temperature field")
        return []
    tiles, widths = [], []
    for ft in features:
        value = ft.get("properties", {}).get(key)
        if not isinstance(value, (int, float)):
            continue
        lat, lon, w, _ = tile_info(ft)
        tiles.append((lat, lon, value))
        if w:
            widths.append(w)
    values = [t[2] for t in tiles]
    print(f"  temperature field: '{key}'   tiles: {len(tiles)}")
    if widths:
        print(f"  median tile width: {statistics.median(widths):.0f} m")
    print(f"  min {min(values):.2f}  mean {statistics.mean(values):.2f}  max {max(values):.2f}"
          f"  std {statistics.pstdev(values):.2f}  distinct values: {len(set(round(v, 4) for v in values))}")
    if isinstance(stats, dict):
        print("  stats_data keys:", list(stats.keys())[:8])
    return tiles


def value_at(tiles, lat, lon):
    nearest = min(tiles, key=lambda t: dist_m(lat, lon, t[0], t[1]))
    return nearest[2], dist_m(lat, lon, nearest[0], nearest[1])


def transect(tiles, lat, west, east, step_m=20):
    print(f"  west-to-east line at latitude {lat} (every {step_m} m):")
    step_deg = step_m / (111320 * math.cos(math.radians(lat)))
    lon, row = west, []
    while lon <= east:
        row.append(value_at(tiles, lat, lon)[0])
        lon += step_deg
    print("   ", " ".join(f"{v:.1f}" for v in row))
    changes = sum(1 for a, b in zip(row, row[1:]) if abs(a - b) > 1e-6)
    print(f"    value changes between neighbouring steps: {changes} of {len(row) - 1}")


def open_meteo(lat, lon):
    r = requests.get("https://archive-api.open-meteo.com/v1/archive", timeout=60, params={
        "latitude": lat, "longitude": lon, "start_date": DATE, "end_date": DATE,
        "hourly": "temperature_2m", "timezone": "UTC"})
    r.raise_for_status()
    temps = r.json()["hourly"]["temperature_2m"]
    hour = int(TIME.split(":")[0])
    as_utc = temps[hour]
    local_as_utc_hour = hour - UTC_OFFSET_HOURS
    as_local = temps[local_as_utc_hour] if 0 <= local_as_utc_hour < 24 else None
    return as_utc, as_local


def main():
    if not KEY:
        sys.exit("Set the FORTYGUARD_API_KEY environment variable first.")

    runs = [("big_100m", BIG_BOX, 100), ("small_20m", SMALL_BOX, 20), ("small_100m", SMALL_BOX, 100)]
    tiles = {}
    for label, box, gran in runs:
        print(f"\n=== {label}: {DATE} {TIME}, granularity {gran} m ===")
        activity = submit_heatmap(box, gran)
        tiles[label] = analyse(label, wait_for(activity)) if activity else []

    print("\n=== Test points: FortyGuard (100 m) vs Open-Meteo ===")
    print(f"{'point':<14}{'FortyGuard':>11}{'tile dist':>11}{'OM if UTC':>11}{'OM if local':>13}")
    for name, (lat, lon) in POINTS.items():
        fg = value_at(tiles["big_100m"], lat, lon) if tiles["big_100m"] else (float("nan"), float("nan"))
        try:
            om_utc, om_local = open_meteo(lat, lon)
        except Exception as exc:  # network or API problem on the reference side
            print("  Open-Meteo failed:", exc)
            om_utc = om_local = float("nan")
        om_local = float("nan") if om_local is None else om_local
        print(f"{name:<14}{fg[0]:>10.1f}C{fg[1]:>9.0f} m{om_utc:>10.1f}C{om_local:>12.1f}C")
    print("Open-Meteo is a coarse reanalysis grid (about 10 km): use it to check the level,")
    print("not the street-level pattern. The column closer to FortyGuard hints at the time zone.")

    for label in ("small_20m", "small_100m"):
        if tiles[label]:
            print(f"\n=== Resolution check: {label} ===")
            transect(tiles[label], TRANSECT_LAT, SMALL_BOX[0], SMALL_BOX[2])


if __name__ == "__main__":
    main()
