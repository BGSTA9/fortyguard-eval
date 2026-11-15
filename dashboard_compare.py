"""
Like-for-like check: request the Dashboard demo's day (20 Jan 2022, single day, 100 m)
from the API and compare with the values clicked on the Dashboard.

Put this file next to fortyguard_eval.py and run:
  python3 dashboard_compare.py
Cost: one heatmap (4,220 credits).
"""
import statistics

import requests

from fortyguard_eval import API, KEY, analyse, box_to_aoi, value_at, wait_for

DATE = "2022-01-20"
BOX = (-112.1550, 33.4650, -112.0000, 33.5350)   # about 43 square miles, inside the demo circle

# (name, lat, lon, value clicked on the Dashboard in Fahrenheit)
DASHBOARD_POINTS = [
    ("West (blue)",     33.470080, -112.151335, 47.62),
    ("Centre",          33.488063, -112.093843, 52.47),
    ("Northeast (red)", 33.531505, -112.005808, 58.40),
]


def to_f(celsius):
    return celsius * 9 / 5 + 32


def main():
    if not KEY:
        raise SystemExit("Set the FORTYGUARD_API_KEY environment variable first.")
    payload = {"polygon_aoi": box_to_aoi(BOX),
               "date_time": {"start_date": DATE, "filter_type": 3},
               "granularity": 100}
    print(f"=== API heatmap: {DATE}, single day, 100 m ===")
    r = requests.post(f"{API}/heatmap", json=payload, timeout=60,
                      headers={"api-key": KEY, "Content-Type": "application/json"})
    print(f"  submit: HTTP {r.status_code}")
    if r.status_code != 200:
        print("  body:", r.text[:500])
        return
    tiles = analyse("dashboard_compare", wait_for(r.json()["data"]["activity_id"]))
    if not tiles:
        return
    values = [t[2] for t in tiles]
    print(f"\n  API range: {to_f(min(values)):.2f} to {to_f(max(values)):.2f} F"
          f"  (spread {(max(values) - min(values)) * 9 / 5:.2f} F,"
          f" std {statistics.pstdev(values) * 9 / 5:.2f} F)")
    print("  Dashboard demo (whole circle): 45.88 to 60.47 F (spread 14.59 F, std 2.50 F)\n")
    print(f"{'point':<17}{'Dashboard':>10}{'API':>9}{'difference':>12}")
    for name, lat, lon, dash_f in DASHBOARD_POINTS:
        api_f = to_f(value_at(tiles, lat, lon)[0])
        print(f"{name:<17}{dash_f:>9.2f}F{api_f:>8.2f}F{api_f - dash_f:>+11.2f}F")


if __name__ == "__main__":
    main()
