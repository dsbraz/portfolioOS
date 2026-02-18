import asyncio
import logging
from contextlib import asynccontextmanager

from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.controllers.board_meeting_controller import router as board_meeting_router
from app.controllers.portfolio_monitoring_controller import router as portfolio_monitoring_router
from app.controllers.deal_controller import router as deal_router
from app.controllers.executive_controller import router as executive_router
from app.controllers.health_controller import router as health_router
from app.controllers.monthly_indicator_controller import router as monthly_indicator_router
from app.controllers.startup_controller import router as startup_router

logger = logging.getLogger("portfolio")


def _run_migrations():
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")


@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, _run_migrations)
    logger.info("Database migrations applied")
    yield


app = FastAPI(
    title="Portfolio API",
    description="Backend API for Portfolio application",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api")
app.include_router(startup_router, prefix="/api")
app.include_router(monthly_indicator_router, prefix="/api")
app.include_router(board_meeting_router, prefix="/api")
app.include_router(executive_router, prefix="/api")
app.include_router(portfolio_monitoring_router, prefix="/api")
app.include_router(deal_router, prefix="/api")
