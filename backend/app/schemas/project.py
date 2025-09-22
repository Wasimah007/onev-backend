"""
Pydantic schemas for project-related operations.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


class ProjectStatus(str, Enum):
    """Project status enumeration."""
    PLANNING = "planning"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ProjectBase(BaseModel):
    """Base project schema with common fields."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: ProjectStatus = ProjectStatus.PLANNING
    budget: Optional[Decimal] = Field(None, ge=0, decimal_places=2)


class ProjectCreate(ProjectBase):
    """Schema for creating a project."""
    department_id: Optional[int] = None
    project_manager_id: Optional[int] = None


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[ProjectStatus] = None
    budget: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    department_id: Optional[int] = None
    project_manager_id: Optional[int] = None


class ProjectResponse(ProjectBase):
    """Schema for project response."""
    id: int
    department_id: Optional[int]
    project_manager_id: Optional[int]
    department_name: Optional[str] = None
    project_manager_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    """Schema for paginated project list response."""
    projects: list[ProjectResponse]
    total: int
    page: int
    page_size: int
    total_pages: int