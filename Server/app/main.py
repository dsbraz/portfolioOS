from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine
from app.controllers.auth_controller import router as auth_router
from app.controllers.auth_dependency import get_current_user
from app.controllers.board_meeting_controller import router as board_meeting_router
from app.controllers.deal_controller import router as deal_router
from app.controllers.executive_controller import router as executive_router
from app.controllers.health_controller import router as health_router
from app.controllers.monthly_indicator_controller import router as monthly_indicator_router
from app.controllers.portfolio_monitoring_controller import router as portfolio_monitoring_router
from app.controllers.report_public_controller import router as report_public_router
from app.controllers.report_token_controller import router as report_token_router
from app.controllers.startup_controller import router as startup_router
from app.controllers.user_controller import router as user_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()


app = FastAPI(
    title="Portfolio API",
    description="Backend API for Portfolio application",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Public routes (no auth required)
app.include_router(health_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(report_public_router, prefix="/api")

# Protected routes (auth required)
protected = [Depends(get_current_user)]
app.include_router(user_router, prefix="/api", dependencies=protected)
app.include_router(startup_router, prefix="/api", dependencies=protected)
app.include_router(monthly_indicator_router, prefix="/api", dependencies=protected)
app.include_router(board_meeting_router, prefix="/api", dependencies=protected)
app.include_router(executive_router, prefix="/api", dependencies=protected)
app.include_router(portfolio_monitoring_router, prefix="/api", dependencies=protected)
app.include_router(deal_router, prefix="/api", dependencies=protected)
app.include_router(report_token_router, prefix="/api", dependencies=protected)
