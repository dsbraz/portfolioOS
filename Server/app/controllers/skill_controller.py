from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

# Built and committed by `scripts/build_skill_pack.py`; nothing is assembled here.
PACK_PATH = Path(__file__).resolve().parents[2] / "static" / "portfolioos.zip"

public_router = APIRouter(tags=["Skills"])


@public_router.get("/skills.zip", response_class=FileResponse)
async def download_skill_pack() -> FileResponse:
    return FileResponse(PACK_PATH, media_type="application/zip", filename="portfolioos.zip")
