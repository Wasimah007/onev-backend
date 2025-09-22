"""
Pydantic schemas for department-related operations.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal


class DepartmentBase(BaseModel):
    """Base department schema with common fields."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    budget: Optional[Decimal] = Field(None, ge=0, decimal_places=2)


class DepartmentCreate(DepartmentBase):
    """Schema for creating a department."""
    manager_id: Optional[int] = None


class DepartmentUpdate(BaseModel):
    """Schema for updating a department."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    budget: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    manager_id: Optional[int] = None


class DepartmentResponse(DepartmentBase):
    """Schema for department response."""
    id: int
    manager_id: Optional[int]
    manager_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DepartmentListResponse(BaseModel):
    """Schema for paginated department list response."""
    departments: list[DepartmentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int