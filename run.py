"""Data server for OpenBB Workspace (http://127.0.0.1:8000).

- Every widget lives in its own file under widgets/ and is registered automatically.
- GET /widgets.json is generated from those files (no hand-edited JSON).
- The OpenBB Platform API (including the 'indonesia' price provider) is served by the same app.
"""

import threading

import uvicorn
from fastapi.responses import JSONResponse
from openbb_core.api.rest_api import app

import widgets
from core.portfolio.reports import warm_up_prices

WIDGET_MODULES = widgets.discover()
widgets.register(app, WIDGET_MODULES)


@app.get("/widgets.json")
def get_widgets():
    return JSONResponse(widgets.widgets_json(WIDGET_MODULES), headers={"Cache-Control": "no-store"})


# Fetch prices, dividends and IHSG for portfolio holdings in the background so the first load is quick.
threading.Thread(target=warm_up_prices, daemon=True).start()


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
