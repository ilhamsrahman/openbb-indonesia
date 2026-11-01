"""Widget registry.

Every module under widgets/ that defines WIDGET (a Workspace widget definition) and/or ROUTES is picked up
automatically:

    WIDGET_ID = "my_widget"          # key in widgets.json
    ORDER = 100                      # position in the widget list (optional)
    WIDGET = {... "endpoint": "/my/endpoint" ...}
    def get(...): ...                # serves WIDGET["endpoint"]; query params = function arguments

    ROUTES = {"/my/options": fn}     # extra endpoints (e.g. dropdown options) without a widget

Add a widget = add a file. Remove a widget = delete its file. Restart run.py afterwards.
"""

import functools
import importlib
import pkgutil


def discover() -> list:
    """Import every widget module (skipping packages) and return those that define WIDGET or ROUTES."""
    mods = []
    for info in pkgutil.walk_packages(__path__, __name__ + "."):
        if info.ispkg:
            continue
        mod = importlib.import_module(info.name)
        if hasattr(mod, "WIDGET") or hasattr(mod, "ROUTES"):
            mods.append(mod)
    return mods


def widgets_json(mods: list) -> dict:
    """The widgets.json document Workspace reads, in ORDER."""
    ws = [m for m in mods if hasattr(m, "WIDGET")]
    ws.sort(key=lambda m: (getattr(m, "ORDER", 10_000), m.WIDGET_ID))
    return {m.WIDGET_ID: m.WIDGET for m in ws}


def routes(mods: list) -> dict:
    """path -> function for every endpoint served by this backend."""
    out = {}
    for m in mods:
        if hasattr(m, "WIDGET") and hasattr(m, "get"):
            out[m.WIDGET["endpoint"]] = m.get
        out.update(getattr(m, "ROUTES", {}))
    return out


def _http(fn, path: str):
    """Turn Python errors into HTTP errors the widget can display (signature kept for FastAPI)."""
    from fastapi import HTTPException

    @functools.wraps(fn)
    def handler(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except FileNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except (ValueError, LookupError) as e:
            if path.startswith("/portfolio"):
                raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:  # show the reason in the widget instead of a blank 500
            raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")
    return handler


def register(app, mods: list) -> None:
    for path, fn in routes(mods).items():
        app.add_api_route(path, _http(fn, path), methods=["GET"], name=fn.__module__ + "." + fn.__name__)
