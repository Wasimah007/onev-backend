
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class SyncFromOneVRequest(BaseModel):
    """Request schema for syncing users from OneV Portal."""
    app_name: str = Field(..., description="Name of the application to sync from (e.g., 'onev')")