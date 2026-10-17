from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from core.config import get_settings
from dependencies import templates
from routers import pages, expenses

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)

# --- Static files ---------------------------------------------------------- #
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- Flask-compatible url_for shim ----------------------------------------- #
# Templates call {{ url_for('route_name') }} and
# {{ url_for('static', filename='...') }} exactly as they did under Flask.
# We inject a wrapper into the Jinja2 environment that delegates to
# Starlette's app.url_path_for(), translating Flask's `filename` kwarg to
# the `path` parameter that StaticFiles expects.
def _url_for(name: str, **kwargs) -> str:
    if name == "static" and "filename" in kwargs:
        kwargs["path"] = kwargs.pop("filename")
    return str(app.url_path_for(name, **kwargs))

templates.env.globals["url_for"] = _url_for

# --- Routers --------------------------------------------------------------- #
app.include_router(pages.router)
app.include_router(expenses.router)

# Placeholder routes preserved from the Flask original
@app.get("/logout", name="logout", response_class=HTMLResponse)
async def logout():
    return "Logout — coming in Step 3"

@app.get("/profile", name="profile", response_class=HTMLResponse)
async def profile():
    return "Profile page — coming in Step 4"

# --- Error handlers -------------------------------------------------------- #
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return templates.TemplateResponse(
            "404.html", {"request": request}, status_code=404
        )
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(str(exc.detail), status_code=exc.status_code)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
