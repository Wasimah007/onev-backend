"""
Pydantic schemas for timesheet-related operations.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


class TimesheetStatus(str, Enum):
    """Timesheet status enumeration."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"


class TimesheetEntryBase(BaseModel):
    """Base timesheet entry schema with common fields."""
    work_date: date
    hours_worked: Decimal = Field(..., ge=0, le=24, decimal_places=2)
    description: Optional[str] = None


class TimesheetEntryCreate(TimesheetEntryBase):
    """Schema for creating a timesheet entry."""
    project_id: int


class TimesheetEntryUpdate(BaseModel):
    """Schema for updating a timesheet entry."""
    work_date: Optional[date] = None
    hours_worked: Optional[Decimal] = Field(None, ge=0, le=24, decimal_places=2)
    description: Optional[str] = None
    project_id: Optional[int] = None


class TimesheetEntryResponse(TimesheetEntryBase):
    """Schema for timesheet entry response."""
    id: int
    user_id: int
    project_id: int
    status: TimesheetStatus
    submitted_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    approved_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    # Related data
    username: Optional[str] = None
    user_full_name: Optional[str] = None
    project_name: Optional[str] = None
    approved_by_username: Optional[str] = None

    class Config:
        from_attributes = True


class TimesheetEntryListResponse(BaseModel):
    """Schema for paginated timesheet entry list response."""
    entries: list[TimesheetEntryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class TimesheetSubmitRequest(BaseModel):
    """Schema for submitting timesheet entries."""
    entry_ids: list[int]


class TimesheetApprovalRequest(BaseModel):
    """Schema for approving/rejecting timesheet entries."""
    entry_ids: list[int]
    action: str = Field(..., regex="^(approve|reject)$")
    comment: Optional[str] = None