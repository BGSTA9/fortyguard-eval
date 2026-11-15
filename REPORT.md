# FORTYGUARD PRODUCTS EVALUATION

Soheil Sanati Moutaban / soheilsanatii@gmail.com

## Summary:

The three products are fast, predictable and easy to start with, and the API's input validation is mostly excellent. The main risks I found are low spatial variation in the 100 m output, a default colour scale that hides this, a demo heatmap that disagrees with the API, and drift between documentation and live behaviour. My suggestions focus on provenance, consistent errors and generated documentation.

## How I evaluated:

Phoenix, AZ, for 15 July 2025 (15:00 and 22:00) and 20 January 2022 (the demo day). I compared downtown, an irrigated park and the airport, used Open-Meteo as an independent check, sent 17 invalid requests to the API, generated a heatmap in the Dashboard, and tested the MCP in Claude Code. I worked with an AI assistant (Claude) throughout this evaluation. It helped me plan the tests, wrote the scripts and helped draft this report. I ran the tests on my account, reviewed every result, and I stand behind the findings. Code: https://github.com/BGSTA9/fortyguard-eval

## 1. UX and UI

- The demo heatmap and guided tour give a quick first result.
- Default colouring uses 12 quantile classes, so a nearly flat map looks as vivid as a varied one. The map I generated spanned only 0.63 °F but was drawn from deep blue to deep red. A continuous scale, or the range shown on the map, would be clearer.
- Point popup: Heat Index has no unit and was higher at the colder point (31.6 at 47.62 °F, 27 at 58.40 °F); UV and Air Quality show "null (Low)" and "null (Good)"; Fahrenheit is mixed with m/s; there is no timestamp.
- The Accuracy Index page explains seven tiers, but I could not find the tier for the map I was viewing.

## 2. Navigation and workflow

- Creating a heatmap takes six clear steps, and the live area readout is helpful.
- The circle tool starts at 62.40 mi², so it has to be resized for a small study area.
- No credit cost is shown before generating; the MCP quotes the cost first.
- After generation the form resets and the previous map stays on screen; the new map has to be opened from the list.
- The email says "pick any US city", but the demo picker lists states; city search appears only inside a map.
- Heatmaps created through the API or MCP do not appear in the Dashboard list.

## 3. Dashboard performance

- A 22.46 mi² heatmap at 100 m generated in under a minute, with a clear success message.
- I did not measure rendering or pan and zoom performance under load.

## 4. API structure and design

- The submit-then-poll design with one status endpoint is clean. Heatmaps finish in about 25 seconds, repeat requests return identical values, and failed requests are not charged.
- There is no point-temperature endpoint; one location requires a polygon request and a search through tiles.
- Environmental Parameters requires temperature as an input. One response mixed a heat index from my 35 °C (33.2 °C) with an apparent temperature from the provider (39.3 °C).

## 5. API documentation

- The response schema example is empty, so tile field names are found only by calling the API.
- Polygon format differs between pages; the time zone of start_time is not stated (it appears to be local).
- Earliest date: the docs and the Dashboard picker say 2019, the API rejects dates before 2021.
- Forecasted heatmaps are advertised, but a future date is rejected.
- MCP docs list 9 tools; the server exposes 11 (Credit Balance and Heatmap Monitoring are undocumented).

## 6. Error handling and validation

- 15 of 17 invalid requests were rejected in about 1 second with clear, field-level messages.
- Two return HTTP 500 instead of 422: a wrongly formatted date (15-07-2025) and a single-hour request without start_time. Both reproduced twice.
- Error bodies have four different shapes across 401, 422, 500 and 405.
- Asynchronous failures give no reason: 3 of 3 requests at 20 m returned only "Failed".

## 7. MCP setup and use

- Setup took one command. Tool descriptions expose cost and safety labels, so the assistant confirmed every paid call before running it.
- The read tool returns only min, max, mean and standard deviation with an empty evidence list, so the assistant could not say where the hottest area was.
- The MCP uses a different auth header from the API and does not offer 20 m.

## 8. Scalability and maintainability

- Results are inline GeoJSON: 2.5 MB for 6,180 tiles. A full-size request at 20 m would be far larger; download links by default or a raster format would scale better.
- Rate limits are mentioned (429) but not quantified.
- Drift between docs and product (tool count, date limits, granularity options, legacy -999 values, double JSON decoding) suggests generating docs from the API schema and adding contract tests.
- A model version field in responses would make results traceable.

## 9. Risks: data consistency

- Low spatial variation. Across 24 mi² of central Phoenix the API range was 0.39 °C at 15:00 and 0.87 °C at 22:00; the park was 0.3 °C cooler than downtown at night. Effective resolution looks coarser than the 100 m grid.
- The demo is an outlier. For 20 January 2022 the demo spans 14.59 °F, while the API spans 1.53 °F over a 43 mi² subset. A heatmap I generated in the Dashboard for 15 July 2025 matched the API closely (103.28 to 103.92 °F against 39.57 to 39.96 °C). Was the demo produced by a different model version or statistic?
- The overall level agrees with Open-Meteo within about 1 °C.
- PM2.5 and PM10 indices were identical (61.1).
- My key is billed at Premium rates, but my balance implies a 1,000,000 credit allowance, not the documented 5,000,000.

## 10. Suggestions, in priority order

- Add per-tile provenance and confidence, and show the accuracy tier in the API and MCP.
- Regenerate or label the demo so it matches current output, and make the colour scale show magnitude.
- Return 422 for the two inputs that give 500, and use one error format.
- Give failure reasons and a coverage lookup for 20 m.
- Return tile locations of extremes in the MCP read tool.
- Generate documentation from the live schema.

## Limits of my evaluation

One city and three dates. I did not test segmentation, Heat Intelligence reports, routing, monitors or load. Open-Meteo is a coarse model, so it checks level, not street-level accuracy.

Best regards,  
SOHEIL SANATI MOUTABAN
