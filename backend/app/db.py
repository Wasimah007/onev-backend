"""
Database connection and raw SQL utilities.
Uses databases library with aiomysql for async MySQL operations.
"""

import logging
from typing import Any, Dict, List, Optional, Union
from databases import Database
from app.config import settings

logger = logging.getLogger(__name__)

# Global database instance
database: Optional[Database] = None


async def get_database() -> Database:
    """Get the database instance."""
    global database
    if database is None:
        raise RuntimeError("Database not initialized. Call connect_db() first.")
    return database


async def connect_db():
    """Initialize database connection pool."""
    global database
    try:
        database = Database(settings.database_url)
        await database.connect()
        logger.info("Database connected successfully")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise


async def disconnect_db():
    """Close database connection pool."""
    global database
    if database:
        await database.disconnect()
        logger.info("Database disconnected")


class DatabaseManager:
    """Database manager for executing raw SQL queries with proper error handling."""
    
    def __init__(self):
        self.db = None
    
    async def get_db(self) -> Database:
        """Get database instance."""
        if self.db is None:
            self.db = await get_database()
        return self.db
    
    async def fetch_one(self, query: str, values: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Execute query and fetch one row."""
        try:
            db = await self.get_db()
            result = await db.fetch_one(query, values or {})
            return dict(result) if result else None
        except Exception as e:
            logger.error(f"Database fetch_one error: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Values: {values}")
            raise
    
    async def fetch_all(self, query: str, values: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Execute query and fetch all rows."""
        try:
            db = await self.get_db()
            results = await db.fetch_all(query, values or {})
            return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Database fetch_all error: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Values: {values}")
            raise
    
    async def execute(self, query: str, values: Dict[str, Any] = None) -> int:
        """Execute query and return affected rows or last insert ID."""
        try:
            db = await self.get_db()
            result = await db.execute(query, values or {})
            return result
        except Exception as e:
            logger.error(f"Database execute error: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Values: {values}")
            raise
    
    async def execute_many(self, query: str, values_list: List[Dict[str, Any]]) -> None:
        """Execute query multiple times with different values."""
        try:
            db = await self.get_db()
            await db.execute_many(query, values_list)
        except Exception as e:
            logger.error(f"Database execute_many error: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Values count: {len(values_list)}")
            raise
    
    async def transaction(self):
        """Start a database transaction context manager."""
        db = await self.get_db()
        return db.transaction()


# Global database manager instance
db_manager = DatabaseManager()


# Common SQL queries for pagination and filtering
def build_pagination_query(
    base_query: str,
    page: int = 1,
    page_size: int = None,
    order_by: str = "id",
    order_direction: str = "ASC"
) -> tuple[str, Dict[str, Any]]:
    """Build paginated query with ordering."""
    if page_size is None:
        page_size = settings.default_page_size
    
    page_size = min(page_size, settings.max_page_size)
    offset = (page - 1) * page_size
    
    # Sanitize order direction
    order_direction = "DESC" if order_direction.upper() == "DESC" else "ASC"
    
    query = f"""
    {base_query}
    ORDER BY {order_by} {order_direction}
    LIMIT :limit OFFSET :offset
    """
    
    values = {
        "limit": page_size,
        "offset": offset
    }
    
    return query, values


def build_count_query(base_query: str) -> str:
    """Convert a SELECT query to a COUNT query."""
    # Simple approach: wrap the base query
    return f"SELECT COUNT(*) as total FROM ({base_query}) as count_subquery"


# Example complex query with joins (commonly needed for timesheet with project info)
async def get_timesheet_entries_with_details(
    user_id: Optional[int] = None,
    project_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = 1,
    page_size: int = None
) -> tuple[List[Dict[str, Any]], int]:
    """
    Get timesheet entries with project and user details using raw SQL joins.
    Returns (entries, total_count).
    """
    # Base query with joins
    base_conditions = ["1=1"]  # Always true condition to simplify WHERE building
    values = {}
    
    if user_id:
        base_conditions.append("t.user_id = :user_id")
        values["user_id"] = user_id
    
    if project_id:
        base_conditions.append("t.project_id = :project_id")
        values["project_id"] = project_id
    
    if start_date:
        base_conditions.append("t.work_date >= :start_date")
        values["start_date"] = start_date
    
    if end_date:
        base_conditions.append("t.work_date <= :end_date")
        values["end_date"] = end_date
    
    where_clause = " AND ".join(base_conditions)
    
    base_query = f"""
    SELECT 
        t.id,
        t.work_date,
        t.hours_worked,
        t.description,
        t.status,
        t.submitted_at,
        t.approved_at,
        t.created_at,
        t.updated_at,
        u.username,
        u.first_name,
        u.last_name,
        p.name as project_name,
        p.status as project_status,
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