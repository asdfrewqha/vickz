# main.py
from contextlib import asynccontextmanager

from app.core.routers_loader import include_all_routers
from app.database.adapter import adapter
from app.core.logging import setup_logging
from app.core.log_middleware import LoggingMiddleware

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    await adapter.initialize_tables()
    yield


def create_app() -> FastAPI:
    setup_logging()

    app = FastAPI(
        title="FastAPI",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
        swagger_ui_parameters={"withCredentials": True},
    )

    include_all_routers(app)
    app.add_middleware(LoggingMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:8000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app


app = create_app()


@app.get("/")
async def redirect():
    return RedirectResponse("/docs")
