import importlib
import pkgutil

from fastapi import FastAPI
from fastapi.routing import APIRouter
import app.api as routers
from app.core.logging import get_logger

logger = get_logger()


def include_all_routers(app: FastAPI):
    for _, module_name, _ in pkgutil.walk_packages(routers.__path__, prefix="app.api."):
        try:
            module = importlib.import_module(module_name)
        except Exception as e:
            logger.error(f"Failed to import module '{module_name}': {e}")
            continue

        router = getattr(module, "router", None)

        if isinstance(router, APIRouter):
            parts = module_name.split(".")
            tag = parts[-3]

            app.include_router(router, tags=[tag], prefix="/api")
            logger.info(f"Included router from: {module_name} (tag: {tag})")
