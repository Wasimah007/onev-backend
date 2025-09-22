"""
Timesheet management routes.
"""

import logging
import math
from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import Dict, Any, Optional
from datetime import date
from app.schemas.timesheet import (
    TimesheetEntryCreate, TimesheetEntryUpdate, TimesheetEntryResponse, 
    TimesheetEntryListResponse, TimesheetSubmitRequest, TimesheetApprovalRequest
)
from app.services.timesheet_service import timesheet_service
from app.auth.router import get_current_user, get_current_admin_user
from app.auth.schemas import MessageResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/timesheet", tags=["Timesheet"])


@router.post("/entries", response_model=TimesheetEntryResponse, status_code=status.HTTP_201_CREATED)
async def create_timesheet_entry(
    entry_data: TimesheetEntryCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Create a new timesheet entry."""
    try:
        entry = await timesheet_service.create_entry(
            user_id=current_user["id"],
            project_id=entry_data.project_id,
            work_date=entry_data.work_date,
            hours_worked=entry_data.hours_worked,
            description=entry_data.description
        )
        
        if entry is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Entry for this project and date already exists or project not found"
            )
        
        return TimesheetEntryResponse(**entry)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create timesheet entry error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create timesheet entry"
        )


@router.get("/entries", response_model=TimesheetEntryListResponse)
async def get_timesheet_entries(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: Optional[int] = Query(None),
    project_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    status: Optional[str] = Query(None),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get paginated list of timesheet entries with filtering."""
    try:
        # Non-admin users can only see their own entries
        if not current_user.get("is_admin", False):
            user_id = current_user["id"]
        
        entries, total_count = await timesheet_service.get_entries(
            page=page,
            page_size=page_size,
            user_id=user_id,
            project_id=project_id,
            start_date=start_date,
            end_date=end_date,
            status=status
        )
        
        total_pages = math.ceil(total_count / page_size) if total_count > 0 else 0
        
        entry_responses = [TimesheetEntryResponse(**entry) for entry in entries]
        
        return TimesheetEntryListResponse(
            entries=entry_responses,
            total=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"Get timesheet entries error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve timesheet entries"
        )


@router.get("/entries/{entry_id}", response_model=TimesheetEntryResponse)
async def get_timesheet_entry(
    entry_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get timesheet entry by ID."""
    try:
        entry = await timesheet_service.get_entry_by_id(entry_id)
        
        if entry is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Timesheet entry not found"
            )
        
        # Users can only view their own entries unless they are admin
        if entry["user_id"] != current_user["id"] and not current_user.get("is_admin", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this timesheet entry"
            )
        
        return TimesheetEntryResponse(**entry)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get timesheet entry error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve timesheet entry"
        )


@router.put("/entries/{entry_id}", response_model=TimesheetEntryResponse)
async def update_timesheet_entry(
    entry_id: int,
    entry_data: TimesheetEntryUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update timesheet entry."""
    try:
        # Check if entry exists and user has permission
        existing_entry = await timesheet_service.get_entry_by_id(entry_id)
        
        if existing_entry is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Timesheet entry not found"
            )
        
        # Users can only update their own entries and only if not submitted/approved
        if existing_entry["user_id"] != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this timesheet entry"
            )
        
        if existing_entry["status"] in ["submitted", "approved"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update submitted or approved timesheet entries"
            )
        
        entry = await timesheet_service.update_entry(
            entry_id=entry_id,
            work_date=entry_data.work_date,
            hours_worked=entry_data.hours_worked,
            description=entry_data.description,
            project_id=entry_data.project_id
        )
        
        if entry is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update entry or duplicate entry exists"
            )
        
        return TimesheetEntryResponse(**entry)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update timesheet entry error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update timesheet entry"
        )


@router.delete("/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_timesheet_entry(
    entry_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete timesheet entry."""
    try:
        # Check if entry exists and user has permission
        existing_entry = await timesheet_service.get_entry_by_id(entry_id)
        
        if existing_entry is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Timesheet entry not found"
            )
        
        # Users can only delete their own entries and only if not submitted/approved
        if existing_entry["user_id"] != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this timesheet entry"
            )
        
        if existing_entry["status"] in ["submitted", "approved"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete submitted or approved timesheet entries"
            )
        
        success = await timesheet_service.delete_entry(entry_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Timesheet entry not found"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete timesheet entry error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete timesheet entry"
        )


@router.post("/entries/submit", response_model=MessageResponse)
async def submit_timesheet_entries(
    submit_data: TimesheetSubmitRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Submit timesheet entries for approval."""
    try:
        success = await timesheet_service.submit_entries(
            entry_ids=submit_data.entry_ids,
            user_id=current_user["id"]
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to submit entries. Check that all entries belong to you and are in draft status."
            )
        
        return MessageResponse(message="Timesheet entries submitted successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Submit timesheet entries error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit timesheet entries"
        )


@router.post("/entries/approve", response_model=MessageResponse)
async def approve_reject_timesheet_entries(
    approval_data: TimesheetApprovalRequest,
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Approve or reject timesheet entries (admin only)."""
    try:
        if approval_data.action == "approve":
            success = await timesheet_service.approve_entries(
                entry_ids=approval_data.entry_ids,
                approved_by=current_user["id"]
            )
            message = "Timesheet entries approved successfully"
        else:  # reject
            success = await timesheet_service.reject_entries(
                entry_ids=approval_data.entry_ids
            )
            message = "Timesheet entries rejected successfully"
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to process entries. Check that all entries are in submitted status."
            )
        
        return MessageResponse(message=message)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Approve/reject timesheet entries error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process timesheet entries"
        )