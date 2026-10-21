from contextlib import asynccontextmanager
from starlette.middleware.sessions import SessionMiddleware

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from core.config import get_settings
from dependencies import templates
from database.db import seed_db
from errors import register_exception_handlers
from routers import pages, expenses, auth, profile
from routers import api_expenses

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Schema is owned by Alembic -- run `alembic upgrade head` by hand after
    # pulling new migrations. Deliberately NOT run here: migrations are a deploy
    # step, and auto-running them means every --reload restart takes DDL locks
    # and multiple workers race the same revision.
    seed_db()
    yield


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)

register_exception_handlers(app)

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

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    same_site="lax",
    https_only=False
)

# --- Routers --------------------------------------------------------------- #
app.include_router(pages.router)
app.include_router(expenses.router)
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(api_expenses.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
