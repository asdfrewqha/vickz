from contextlib import asynccontextmanager

from app.core.log_middleware import LoggingMiddleware
from app.core.logging import setup_logging
from app.core.routers_loader import include_all_routers
from app.core.settings import settings
from app.database.adapter import adapter
from app.utils.s3_adapter import S3HttpxSigV4Adapter
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    await adapter.initialize_tables()

    s3_b1 = S3HttpxSigV4Adapter(settings.s3_settings.bucket1)
    s3_b2 = S3HttpxSigV4Adapter(settings.s3_settings.bucket2)
    app.state.s3_b1 = s3_b1
    app.state.s3_b2 = s3_b2

    yield

    await s3_b1.client.aclose()
    await s3_b2.client.aclose()


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
