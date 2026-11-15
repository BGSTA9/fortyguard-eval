# FortyGuard Evaluation

This repository contains my evaluation of the FortyGuard Temperature Dashboard, API and MCP, using Phoenix, AZ as the test area. It holds the scripts I used to call the API and the written report with my findings and suggestions.

## Scripts

| Script | What it does |
| --- | --- |
| `fortyguard_eval.py` | Requests 100 m and 20 m heatmaps, reads the temperature at three test points (downtown, an irrigated park and the airport) and compares them with Open-Meteo. Takes an optional hour argument, such as `22:00` (default `15:00`). |
| `dashboard_compare.py` | Requests the Dashboard demo day (20 January 2022) from the API so it can be compared with the demo heatmap. |
| `error_tests.py` | Sends 17 invalid requests to test the API's input validation and error responses. |

`dashboard_compare.py` and `error_tests.py` import helpers from `fortyguard_eval.py`, so keep the three files in the same folder.

## How to run

```bash
export FORTYGUARD_API_KEY='your-key'
pip install requests
python3 fortyguard_eval.py        # or: python3 fortyguard_eval.py 22:00
python3 dashboard_compare.py
python3 error_tests.py
```

The scripts read the key only from the `FORTYGUARD_API_KEY` environment variable. Heatmap requests use FortyGuard credits.

## Report

The full findings are in [REPORT.md](REPORT.md).

## Note on data

The raw API result files (`result_*.json`) that the scripts write are excluded from this repository via `.gitignore`.
