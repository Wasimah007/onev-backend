"""
User service with raw SQL operations.
"""

import logging
from typing import Optional, Dict, Any, List, Tuple
from app.db import db_manager, build_pagination_query, build_count_query
# from app.timsheet_db import db_manager, build_pagination_query, build_count_query
from app.utils.passwords import hash_password

logger = logging.getLogger(__name__)


class UserService:
    """User service using raw SQL."""
    
    async def create_user(
        self,
        email: str,
        username: str,
        password: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        group: Optional[str] = None,
        # department_id: Optional[int] = None,
        is_admin: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Create a new user."""
        try:
            # Check if user already exists
            existing_user = await self.get_user_by_email_or_username(email, username)
            if existing_user:
                return None
            
            # Hash password
            password_hash = hash_password(password)
            
            # Insert user
            query = """
            INSERT INTO users (email, username, password_hash, first_name, last_name,`group`)
            VALUES (:email, :username, :password_hash, :first_name, :last_name,:group)
            """
            
            values = {
                "email": email,
                "username": username,
                "password_hash": password_hash,
                "first_name": first_name,
                "last_name": last_name,
                "group": group
                # "department_id": department_id,
                # "is_admin": is_admin
            }
            
            user_id = await db_manager.execute(query, values)
            
            # Return created user
            return await self.get_user_by_id(user_id)
            
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise
    
    async def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID with department info."""
        query = """
        SELECT u.users_id, u.email, u.username, u.first_name, u.last_name, 
               u.is_active, u.created_at, u.updated_at
        FROM users u
			WHERE u.users_id = :users_id;
        """
        
        values = {"users_id": user_id}
        return await db_manager.fetch_one(query, values)
    
    async def get_user_by_email_or_username(self, email: str, username: str) -> Optional[Dict[str, Any]]:
        """Get user by email or username."""
        query = """
        SELECT users_id, email, username, password_hash, first_name, last_name, 
               is_active, created_at, updated_at
        FROM users 
        WHERE email = :email OR username = :username
        """
        
        values = {"email": email, "username": username}
        return await db_manager.fetch_one(query, values)
    
    async def get_users(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        # department_id: Optional[int] = None,
        is_active: Optional[bool] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Get paginated list of users with filtering."""
        # Build WHERE conditions
        conditions = ["1=1"]
        values = {}
        
        if search:
            conditions.append("(u.username LIKE :search OR u.email LIKE :search OR u.first_name LIKE :search OR u.last_name LIKE :search)")
            values["search"] = f"%{search}%"
        
        # if department_id is not None:
        #     conditions.append("u.department_id = :department_id")
        #     values["department_id"] = department_id
        
        if is_active is not None:
            conditions.append("u.is_active = :is_active")
            values["is_active"] = is_active
        
        where_clause = " AND ".join(conditions)
        
        # Base query
        base_query = f"""
        SELECT u.users_id, u.email, u.username, u.first_name, u.last_name, 
               u.is_active,u.created_at, u.updated_at
        FROM users u
        """
        
        # Get total count
        count_query = build_count_query(base_query)
        count_result = await db_manager.fetch_one(count_query, values)
        total_count = count_result["total"] if count_result else 0
        
        # Get paginated results
        paginated_query, pagination_values = build_pagination_query(
            base_query, page, page_size, "u.created_at", "DESC"
        )
        
        # Merge values
        all_values = {**values, **pagination_values}
        
        users = await db_manager.fetch_all(paginated_query, all_values)
        
        return users, total_count
    
    async def update_user(
        self,
        user_id: int,
        email: Optional[str] = None,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        # department_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        is_admin: Optional[bool] = None
    ) -> Optional[Dict[str, Any]]:
        """Update user information."""
        try:
            # Build update fields
            update_fields = []
            values = {"users_id": user_id}
            
            if email is not None:
                # Check if email is already taken by another user
                existing = await db_manager.fetch_one(
                    "SELECT users_id FROM users WHERE email = :email AND users_id != :users_id",
                    {"email": email, "users_id": user_id}
                )
                if existing:
                    return None
                update_fields.append("email = :email")
                values["email"] = email
            
            if username is not None:
                # Check if username is already taken by another user
                existing = await db_manager.fetch_one(
                    "SELECT users_id FROM users WHERE username = :username AND users_id != :users_id",
                    {"username": username, "users_id": user_id}
                )
                if existing:
                    return None
                update_fields.append("username = :username")
                values["username"] = username
            
            if first_name is not None:
                update_fields.append("first_name = :first_name")
                values["first_name"] = first_name
            
            if last_name is not None:
                update_fields.append("last_name = :last_name")
                values["last_name"] = last_name
            
            # if department_id is not None:
            #     update_fields.append("department_id = :department_id")
            #     values["department_id"] = department_id
            
            if is_active is not None:
                update_fields.append("is_active = :is_active")
                values["is_active"] = is_active
            
            if is_admin is not None:
                update_fields.append("is_admin = :is_admin")
                values["is_admin"] = is_admin
            
            if not update_fields:
                return await self.get_user_by_id(user_id)
            
            update_fields.append("updated_at = NOW()")
            
            query = f"""
            UPDATE users 
            SET {', '.join(update_fields)}
            WHERE users_id = :users_id
            """
            
            result = await db_manager.execute(query, values)
            
            if result > 0:
                return await self.get_user_by_id(user_id)
            
            return None
            
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            raise
    
    async def delete_user(self, user_id: int) -> bool:
        """Soft delete user by setting is_active to False."""
        try:
            query = """
            UPDATE users 
            SET is_active = FALSE, updated_at = NOW()
            WHERE users_id = :users_id
            """
            
            values = {"users_id": user_id}
            result = await db_manager.execute(query, values)
            
            return result > 0
            
        except Exception as e:
            logger.error(f"Error deleting user: {e}")
            raise


# Global user service instance
user_service = UserService()