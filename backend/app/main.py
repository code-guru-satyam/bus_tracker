from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.routes.bus_router import router as bus_router
from app.routes.location_router import router as location_router
from app.routes.route_router import router as route_router
from app.websocket.bus_location_ws import router as bus_location_ws_router


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("Starting UP Bus Tracker API")
    yield
    logger.info("Shutting down UP Bus Tracker API")


app = FastAPI(
    title="UP Bus Tracker API",
    description="Real-time bus tracking platform backend.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
def health_check(db: Session = Depends(get_db)) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "ok"}


app.include_router(route_router, prefix="/api/v1")
app.include_router(bus_router, prefix="/api/v1")
app.include_router(location_router, prefix="/api/v1")
app.include_router(bus_location_ws_router)
