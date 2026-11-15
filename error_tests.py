"""
FortyGuard API - error handling and validation tests.

Sends deliberately invalid requests and records how the API responds.
Put this file next to fortyguard_eval.py and run:
  python3 error_tests.py
Invalid requests are documented as free. If the API accepts one and completes it,
that request costs 4,220 credits and is worth reporting.
"""
import copy
import time

import requests

from fortyguard_eval import API, KEY, box_to_aoi

SMALL_BOX = (-112.0800, 33.4450, -112.0700, 33.4530)   # downtown Phoenix, under 1 square mile
GOOD = {"polygon_aoi": box_to_aoi(SMALL_BOX),
        "date_time": {"start_date": "2025-07-15", "start_time": "15:00", "filter_type": 1},
        "granularity": 100}
HEADERS = {"api-key": KEY or "", "Content-Type": "application/json"}
results = []


def variant(change):
    payload = copy.deepcopy(GOOD)
    change(payload)
    return payload


def poll(activity_id, max_seconds=150):
    """Follow an accepted request to its final status."""
    t0 = time.time()
    while time.time() - t0 < max_seconds:
        r = requests.get(f"{API}/status/{activity_id}", headers={"api-key": KEY}, timeout=60)
        if r.status_code == 200:
            data = r.json().get("data", {})
            status = str(data.get("status", ""))
            if status.lower() in ("completed", "succeeded"):
                return "ACCEPTED then Completed (charged)"
            if status.lower() in ("failed", "error"):
                extra = {k: v for k, v in data.items() if k not in ("activity_id", "task_id", "status")}
                return f"ACCEPTED then Failed; reason given: {extra or 'none'}"
        time.sleep(5)
    return "ACCEPTED, still processing after 150 s"


def run(name, expected, method="POST", path="/heatmap", headers=None, payload=None, raw=None):
    headers = HEADERS if headers is None else headers
    t0 = time.time()
    try:
        if raw is not None:
            r = requests.request(method, API + path, headers=headers, data=raw, timeout=60)
        elif payload is not None:
            r = requests.request(method, API + path, headers=headers, json=payload, timeout=60)
        else:
            r = requests.request(method, API + path, headers=headers, timeout=60)
    except Exception as exc:
        results.append((name, expected, "no response", 0.0, str(exc)[:120]))
        return
    elapsed = time.time() - t0
    body = " ".join(r.text.split())[:160]
    outcome = body
    if r.status_code == 200 and method == "POST":
        try:
            outcome = poll(r.json()["data"]["activity_id"])
        except Exception:
            pass
    results.append((name, expected, r.status_code, elapsed, outcome))
    print(f"[{len(results):>2}] {name}: HTTP {r.status_code} in {elapsed:.1f}s")


def main():
    if not KEY:
        raise SystemExit("Set the FORTYGUARD_API_KEY environment variable first.")

    run("Missing API key", "401", headers={"Content-Type": "application/json"}, payload=GOOD)
    run("Wrong API key", "401", headers={"api-key": "not-a-real-key", "Content-Type": "application/json"}, payload=GOOD)
    run("Malformed JSON body", "400/422", raw="{not json")
    run("Empty body", "400/422", payload={})
    run("Missing date_time", "400/422", payload=variant(lambda p: p.pop("date_time")))
    run("Missing polygon_aoi", "400/422", payload=variant(lambda p: p.pop("polygon_aoi")))
    run("Date in wrong format (15-07-2025)", "400/422",
        payload=variant(lambda p: p["date_time"].update(start_date="15-07-2025")))
    run("Single hour without start_time", "400/422",
        payload=variant(lambda p: p["date_time"].pop("start_time")))
    run("Invalid filter_type (9)", "400/422",
        payload=variant(lambda p: p["date_time"].update(filter_type=9)))
    run("Invalid granularity (10)", "400/422", payload=variant(lambda p: p.update(granularity=10)))
    run("Date before 2019 (2010-07-15)", "400/422",
        payload=variant(lambda p: p["date_time"].update(start_date="2010-07-15")))
    run("Future date (2030-07-15)", "400/422 or clear message",
        payload=variant(lambda p: p["date_time"].update(start_date="2030-07-15")))

    def unclose(p):
        p["polygon_aoi"]["features"][0]["geometry"]["coordinates"][0].pop()
    run("Polygon not closed", "400", payload=variant(unclose))

    run("Coordinates outside the US (London)", "400",
        payload=variant(lambda p: p.update(polygon_aoi=box_to_aoi((-0.13, 51.50, -0.12, 51.51)))))
    run("Area above the 50 sq mi limit", "400/403",
        payload=variant(lambda p: p.update(polygon_aoi=box_to_aoi((-112.30, 33.30, -111.90, 33.70)))))
    run("Status of an unknown activity id", "404", method="GET",
        path="/status/00000000-0000-0000-0000-000000000000")
    run("GET on a POST endpoint", "405", method="GET", path="/heatmap")

    print("\n=== Summary ===")
    for i, (name, expected, code, elapsed, outcome) in enumerate(results, 1):
        print(f"{i:>2}. {name}")
        print(f"    expected {expected} | got HTTP {code} in {elapsed:.1f}s")
        print(f"    {outcome}")


if __name__ == "__main__":
    main()

