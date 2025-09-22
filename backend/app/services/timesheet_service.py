"""
Timesheet service with raw SQL operations.
"""

import logging
from typing import Optional, Dict, Any, List, Tuple
from datetime import date, datetime
from decimal import Decimal
from app.db import db_manager, build_pagination_query, build_count_query

logger = logging.getLogger(__name__)


class TimesheetService:
    """Timesheet service using raw SQL."""
    
    async def create_entry(
        self,
        user_id: int,
        project_id: int,
        work_date: date,
        hours_worked: Decimal,
        description: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Create a new timesheet entry."""
        try:
            # Check if project exists and user has access
            project_check = await db_manager.fetch_one(
                "SELECT id FROM projects WHERE id = :project_id",
                {"project_id": project_id}
            )
            
            if not project_check:
                return None
            
            # Insert entry
            query = """
            INSERT INTO timesheet_entries (user_id, project_id, work_date, hours_worked, description)
            VALUES (:user_id, :project_id, :work_date, :hours_worked, :description)
            """
            
            values = {
                "user_id": user_id,
                "project_id": project_id,
                "work_date": work_date,
                "hours_worked": hours_worked,
                "description": description
            }
            
            entry_id = await db_manager.execute(query, values)
            
            # Return created entry
            return await self.get_entry_by_id(entry_id)
            
        except Exception as e:
            logger.error(f"Error creating timesheet entry: {e}")
            if "Duplicate entry" in str(e) or "unique_user_project_date" in str(e):
                return None
            raise
    
    async def get_entry_by_id(self, entry_id: int) -> Optional[Dict[str, Any]]:
        """Get timesheet entry by ID with related data."""
        query = """
        SELECT 
            t.id, t.user_id, t.project_id, t.work_date, t.hours_worked, 
            t.description, t.status, t.submitted_at, t.approved_at, 
            t.approved_by, t.created_at, t.updated_at,
            u.username, 
            CONCAT(u.first_name, ' ', u.last_name) as user_full_name,
            p.name as project_name,
            approver.username as approved_by_username
        FROM timesheet_entries t
        JOIN users u ON t.user_id = u.id
        JOIN projects p ON t.project_id = p.id
        LEFT JOIN users approver ON t.approved_by = approver.id
        WHERE t.id = :entry_id
        """
        
        values = {"entry_id": entry_id}
        return await db_manager.fetch_one(query, values)
    
    async def get_entries(
        self,
        page: int = 1,
        page_size: int = 20,
        user_id: Optional[int] = None,
        project_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        status: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Get paginated list of timesheet entries with filtering."""
        # Build WHERE conditions
        conditions = ["1=1"]
        values = {}
        
        if user_id is not None:
            conditions.append("t.user_id = :user_id")
            values["user_id"] = user_id
        
        if project_id is not None:
            conditions.append("t.project_id = :project_id")
            values["project_id"] = project_id
        
        if start_date is not None:
            conditions.append("t.work_date >= :start_date")
            values["start_date"] = start_date
        
        if end_date is not None:
            conditions.append("t.work_date <= :end_date")
            values["end_date"] = end_date
        
        if status is not None:
            conditions.append("t.status = :status")
            values["status"] = status
        
        where_clause = " AND ".join(conditions)
        
        # Base query
        base_query = f"""
        SELECT 
            t.id, t.user_id, t.project_id, t.work_date, t.hours_worked, 
            t.description, t.status, t.submitted_at, t.approved_at, 
            t.approved_by, t.created_at, t.updated_at,
            u.username, 
            CONCAT(u.first_name, ' ', u.last_name) as user_full_name,
            p.name as project_name,
            approver.username as approved_by_username
        FROM timesheet_entries t
        JOIN users u ON t.user_id = u.id
        JOIN projects p ON t.project_id = p.id
        LEFT JOIN users approver ON t.approved_by = approver.id
        WHERE {where_clause}
        """
        
        # Get total count
        count_query = build_count_query(base_query)
        count_result = await db_manager.fetch_one(count_query, values)
        total_count = count_result["total"] if count_result else 0
        
        # Get paginated results
        paginated_query, pagination_values = build_pagination_query(
            base_query, page, page_size, "t.work_date", "DESC"
        )
        
        # Merge values
        all_values = {**values, **pagination_values}
        
        entries = await db_manager.fetch_all(paginated_query, all_values)
        
        return entries, total_count
    
    async def update_entry(
        self,
        entry_id: int,
        work_date: Optional[date] = None,
        hours_worked: Optional[Decimal] = None,
        description: Optional[str] = None,
        project_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Update timesheet entry."""
        try:
            # Build update fields
            update_fields = []
            values = {"entry_id": entry_id}
            
            if work_date is not None:
                update_fields.append("work_date = :work_date")
                values["work_date"] = work_date
            
            if hours_worked is not None:
                update_fields.append("hours_worked = :hours_worked")
                values["hours_worked"] = hours_worked
            
            if description is not None:
                update_fields.append("description = :description")
                values["description"] = description
            
            if project_id is not None:
                # Check if project exists
                project_check = await db_manager.fetch_one(
                    "SELECT id FROM projects WHERE id = :project_id",
                    {"project_id": project_id}
                )
                if not project_check:
                    return None
                
                update_fields.append("project_id = :project_id")
                values["project_id"] = project_id
            
            if not update_fields:
                return await self.get_entry_by_id(entry_id)
            
            update_fields.append("updated_at = NOW()")
            
            query = f"""
            UPDATE timesheet_entries 
            SET {', '.join(update_fields)}
            WHERE id = :entry_id
            """
            
            result = await db_manager.execute(query, values)
            
            if result > 0:
                return await self.get_entry_by_id(entry_id)
            
            return None
            
        except Exception as e:
            logger.error(f"Error updating timesheet entry: {e}")
            if "Duplicate entry" in str(e) or "unique_user_project_date" in str(e):
                return None
            raise
    
    async def delete_entry(self, entry_id: int) -> bool:
        """Delete timesheet entry."""
        try:
            query = "DELETE FROM timesheet_entries WHERE id = :entry_id"
            values = {"entry_id": entry_id}
            result = await db_manager.execute(query, values)
            
            return result > 0
            
        except Exception as e:
            logger.error(f"Error deleting timesheet entry: {e}")
            raise
    
    async def submit_entries(self, entry_ids: List[int], user_id: int) -> bool:
        """Submit timesheet entries for approval."""
        try:
            async with await db_manager.transaction():
                # Check that all entries belong to the user and are in draft status
                check_query = """
                SELECT COUNT(*) as count
                FROM timesheet_entries 
                WHERE id IN :entry_ids AND user_id = :user_id AND status = 'draft'
                """
                
                # Convert list to tuple for SQL IN clause
                entry_ids_tuple = tuple(entry_ids)
                check_result = await db_manager.fetch_one(
                    check_query.replace(":entry_ids", str(entry_ids_tuple)),
                    {"user_id": user_id}
                )
                
                if check_result["count"] != len(entry_ids):
                    return False
                
                # Update entries to submitted status
                update_query = f"""
                UPDATE timesheet_entries 
                SET status = 'submitted', submitted_at = NOW(), updated_at = NOW()
                WHERE id IN {entry_ids_tuple}
                """
                
                await db_manager.execute(update_query)
                
                return True
                
        except Exception as e:
            logger.error(f"Error submitting timesheet entries: {e}")
            raise
    
    async def approve_entries(self, entry_ids: List[int], approved_by: int) -> bool:
        """Approve timesheet entries."""
        try:
            async with await db_manager.transaction():
                # Check that all entries are in submitted status
                check_query = """
                SELECT COUNT(*) as count
                FROM timesheet_entries 
                WHERE id IN :entry_ids AND status = 'submitted'
                """
                
                entry_ids_tuple = tuple(entry_ids)
                check_result = await db_manager.fetch_one(
                    check_query.replace(":entry_ids", str(entry_ids_tuple)),
                    {}
                )
                
                if check_result["count"] != len(entry_ids):
                    return False
                
                # Update entries to approved status
                update_query = f"""
                UPDATE timesheet_entries 
                SET status = 'approved', approved_at = NOW(), approved_by = {approved_by}, updated_at = NOW()
                WHERE id IN {entry_ids_tuple}
                """
                
                await db_manager.execute(update_query)
                
                return True
                
        except Exception as e:
            logger.error(f"Error approving timesheet entries: {e}")
            raise
    
    async def reject_entries(self, entry_ids: List[int]) -> bool:
        """Reject timesheet entries (back to draft)."""
        try:
            async with await db_manager.transaction():
                # Check that all entries are in submitted status
                check_query = """
                SELECT COUNT(*) as count
                FROM timesheet_entries 
                WHERE id IN :entry_ids AND status = 'submitted'
                """
                
                entry_ids_tuple = tuple(entry_ids)
                check_result = await db_manager.fetch_one(
                    check_query.replace(":entry_ids", str(entry_ids_tuple)),
                    {}
                )
                
                if check_result["count"] != len(entry_ids):
                    return False
                
                # Update entries back to draft status
                update_query = f"""
                UPDATE timesheet_entries 
                SET status = 'rejected', updated_at = NOW()
                WHERE id IN {entry_ids_tuple}
                """
                
                await db_manager.execute(update_query)
                
                return True
                
        except Exception as e:
            logger.error(f"Error rejecting timesheet entries: {e}")
            raise


# Global timesheet service instance
timesheet_service = TimesheetService()