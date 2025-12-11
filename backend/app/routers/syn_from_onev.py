from fastapi import APIRouter, HTTPException
from app.services.onev_sync_service import sync_from_onev
from app.schemas.sync_from_onev import SyncFromOneVRequest

router = APIRouter(prefix="/api/users", tags=["User Sync"])

@router.post("/sync_from_onev")
async def sync_users(request: SyncFromOneVRequest):
    """
    Copy users , role and user roles from oneV.
    """
    try:
        result = await sync_from_onev(request.app_name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
