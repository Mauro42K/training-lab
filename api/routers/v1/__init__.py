from fastapi import APIRouter, Depends

from api.dependencies.auth import require_api_key
from api.routers.v1.daily import router as daily_router
from api.routers.v1.ingest import router as ingest_router
from api.routers.v1.training_load import router as training_load_router
from api.routers.v1.workouts import router as workouts_router

router = APIRouter(prefix="/v1", tags=["v1"], dependencies=[Depends(require_api_key)])
router.include_router(ingest_router)
router.include_router(workouts_router)
router.include_router(daily_router)
router.include_router(training_load_router)
