from fastapi import APIRouter, Depends, HTTPException, status

from api.dependencies.auth import require_api_key


def build_v1_router() -> APIRouter:
    router = APIRouter(
        prefix="/v1",
        tags=["v1"],
        dependencies=[Depends(require_api_key)],
    )

    @router.get("/workouts")
    def workouts_placeholder() -> None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="/v1/workouts will be implemented in Block 5",
        )

    return router
