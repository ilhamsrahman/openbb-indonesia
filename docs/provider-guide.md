> **Background note:** this guide was written for the first, single-file version of the project (one `run.py`
> and a hand-edited `widgets.json`). The provider part (`openbb_indonesia/`) is unchanged; for the current layout
> (`core/` + one file per widget in `widgets/`) see the README.

# OpenBB Custom Provider Guide: `openbb-indonesia`

A reference guide for how this project is structured, how to turn it on,
and how data actually flows from your Python code to a widget on the
OpenBB Workspace dashboard.

---

## 1. Folder Structure

```
openbb-indonesia/                  ← project root
│
├── pyproject.toml                 ← package metadata + entry point registration
├── run.py                         ← launches the server (start here every time)
├── widgets.json                   ← tells Workspace what widgets exist
│
├── openbb_indonesia/              ← the actual Python package
│   ├── __init__.py                ← defines the Provider object
│   └── fetchers.py                ← defines the Fetcher (the real data logic)
│
└── openbb_indonesia.egg-info/     ← AUTO-GENERATED — do not edit by hand
    ├── PKG-INFO
    ├── SOURCES.txt
    ├── dependency_links.txt
    ├── entry_points.txt           ← how openbb_core actually finds your provider
    ├── requires.txt
    └── top_level.txt
```

**Rule of thumb:** you only ever hand-edit 4 files:
`pyproject.toml`, `run.py`, `widgets.json`, `__init__.py`, `fetchers.py`.
Everything in `egg-info/` is regenerated automatically when you install the package.

---

## 2. What Each File Actually Does

| File | Role |
|---|---|
| `fetchers.py` | The actual data logic. Defines how a request becomes a query, how data is pulled, and how it's shaped into OpenBB's standard data model. |
| `__init__.py` | Wraps your fetcher(s) into a `Provider` object with a name (`"indonesia"`) — this is the string you'll type into the `provider` param anywhere in OpenBB. |
| `pyproject.toml` | Declares the package name/version, dependencies, and — critically — the `entry-points` block that lets `openbb_core` auto-discover your provider without you writing any registration code. |
| `run.py` | Boots the actual web server (`uvicorn`) that hosts OpenBB's REST API *and* serves your `widgets.json` at `/widgets.json`. |
| `widgets.json` | Tells OpenBB Workspace: what widgets exist, what endpoint to call, what parameters to show, and how to read the response. |

---

## 3. How to Turn It On (every time)

1. **Activate your conda environment** (the one with `openbb-core`, `httpx`, and your package installed):
   ```
   conda activate openbb
   ```
2. **From the project root**, run the server:
   ```
   python run.py
   ```
   You should see:
   ```
   INFO:     Uvicorn running on http://127.0.0.1:8000
   INFO:     Application startup complete.
   ```
   ⚠️ You must run this from the folder containing `widgets.json`, since `run.py` loads it with a relative path.

3. **In OpenBB Workspace**, go to **Edit backend** and confirm:
   - Name: anything memorable, e.g. `openbb-indonesia`
   - Endpoint URL: `http://127.0.0.1:8000/`
   - Click **Test** → should succeed → click **Update**

4. **Add the widget** to a dashboard (or remove/re-add it if you changed `widgets.json`).

That's it — steps 1–2 are your daily "turn it on" routine; step 3–4 only need repeating when you change `widgets.json` or restart your machine.

---

## 4. One-Time Setup (only needed once, or after changing fetcher/provider code)

Any time you change `fetchers.py`, `__init__.py`, or `pyproject.toml`, reinstall the package in **editable mode** so `openbb_core` picks up the change:

```
pip install -e .
```

This regenerates the `egg-info/` folder and (re)registers your provider via the entry point:

```
[openbb_provider_extension]
indonesia = openbb_indonesia:provider
```

If you skip this after a fresh clone or a code change, `openbb_core` won't know your provider exists, or will run stale code.

---

## 5. The Full Data Flow

Here's what happens, end to end, when Workspace loads your widget:

```
┌─────────────────────┐
│  OpenBB Workspace    │
│  (your dashboard)    │
└──────────┬───────────┘
           │ 1. GET /widgets.json
           ▼
┌─────────────────────────────┐
│  run.py (uvicorn @ :8000)   │  ← serves widgets.json from disk
└──────────┬───────────────────┘
           │ 2. Workspace reads widget config:
           │    endpoint, params, dataKey
           ▼
┌──────────────────────────────────────────────┐
│  GET /api/v1/equity/price/historical           │
│      ?symbol=BBCA&provider=indonesia           │
└──────────┬─────────────────────────────────────┘
           │ 3. openbb_core routes this to your provider
           │    because provider=indonesia matches your
           │    entry_points registration
           ▼
┌───────────────────────────────┐
│  IndoEquityHistoricalFetcher   │
│  (fetchers.py)                 │
│                                 │
│  transform_query(params)       │ → builds EquityHistoricalQueryParams
│  aextract_data(query, creds)   │ → returns raw list[dict] (your mock data)
│  transform_data(query, data)   │ → converts to list[EquityHistoricalData]
└──────────┬──────────────────────┘
           │ 4. openbb_core wraps the result in an OBBject:
           │    { "results": [...], "provider": "indonesia", ... }
           ▼
┌─────────────────────────────────────┐
│  Workspace reads "dataKey": "results" │  ← THE CRITICAL FIX
│  → unwraps the nested array           │
└──────────┬─────────────────────────────┘
           │ 5. Renders as a table (or chart) widget
           ▼
┌─────────────────────┐
│  Widget on dashboard │
└─────────────────────┘
```

**Key insight from this whole exercise:** OpenBB's REST API never returns a
flat array — it always wraps results in an "OBBject" envelope
(`results`, `provider`, `warnings`, `chart`, `extra`). Workspace's generic
custom-backend widgets expect *flat* JSON by default, so `widgets.json`
must explicitly say where the real data lives with:

```json
"data": { "dataKey": "results" }
```

Without this, requests succeed (HTTP 200) and data is fetched correctly,
but the widget appears completely empty — because Workspace is looking
for rows at the top level of the response and finding none.

---

## 6. `widgets.json` Anatomy (annotated)

```json
{
  "indonesian_historical_price": {          // ← internal widget ID
    "name": "Indonesian Stock Chart",        // shown in the widget header
    "description": "...",                    // shown in widget picker
    "category": "equity",                    // for organizing the widget catalog
    "type": "table",                         // "table" or "chart"
    "endpoint": "/api/v1/equity/price/historical",
    "data": { "dataKey": "results" },        // ← unwraps the OBBject response
    "gridData": { "w": 8, "h": 12 },         // default widget size on dashboard
    "params": [
      {
        "paramName": "symbol",
        "type": "text",
        "value": "BBCA",                     // default value
        "label": "Symbol",                   // shown to the user
        "show": true                         // visible/editable on the widget
      },
      {
        "paramName": "provider",
        "type": "text",
        "value": "indonesia",
        "label": "Provider",
        "show": true
      }
    ]
  }
}
```

---

## 7. Quick Troubleshooting Reference

| Symptom | Likely Cause | Fix |
|---|---|---|
| `Field required` error, `symbol`/`provider` shown as `null` | Workspace has a stale cached widget config | Remove and re-add the widget |
| "Widget Unavailable — URL not accessible" | `run.py` isn't running, or crashed on startup | Restart `run.py`, check terminal for tracebacks |
| `TypeError: transform_query() got an unexpected keyword argument 'params'` | Fetcher method signatures don't match what `openbb_core` calls | Match signatures: `transform_query(cls, params: dict)` |
| 200 OK in logs, but widget is blank | Response is nested (`results` key), Workspace expects flat data | Add `"data": {"dataKey": "results"}` to `widgets.json` |
| `GET /apps.json`, `/agents.json`, `/templates.json` → 404 | Normal — these are optional Workspace features you haven't built | Ignore, harmless |

---

## 8. Next Steps (optional, for real charts)

To move from a table to an actual candlestick/line chart:

1. `pip install openbb-charting`
2. Add a hidden param to `widgets.json`: `{"paramName": "chart", "type": "text", "value": "true", "label": "Chart", "show": false}`
3. Change `"type": "table"` → `"type": "chart"`
4. Restart `run.py`, remove/re-add the widget
5. Expand your mock data beyond 2 points so the chart is meaningful to look at
