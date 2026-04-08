from fastapi import APIRouter

from v1.summaries import router as summaries_router
from v1.transcribes import router as transcribes_router

router = APIRouter()

router.include_router(transcribes_router, prefix="/transcribes", tags=["transcribes"])
router.include_router(summaries_router, prefix="/summaries", tags=["summaries"])
