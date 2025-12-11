"""
Authentication service with raw SQL operations.
Updated to work with UUID-based schema.
"""

import logging
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from app.db import db_manager
from app.utils.passwords import hash_password, verify_password
from app.auth.jwt import create_access_token, create_refresh_token, verify_token
from app.config import settings
from fastapi import HTTPException
from app.config import settings
import httpx
from app.auth.azure_verify import verify_azure_token
from jwt.algorithms import RSAAlgorithm
import jwt

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service using raw SQL with UUID schema."""
    
    async def create_user(
        self, 
        email: str, 
        username: str, 
        password: str,
        first_name: str,
        last_name: str,
        group: str = "Employee",
        phone: Optional[str] = None,
        department: Optional[str] = None,
        employee_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Create a new user with hashed password."""
        try:
            # Check if user already exists
            existing_user = await self.get_user_by_email_or_username(email, username)
            if existing_user:
                return None
            
            # Hash password
            password_hash = hash_password(password)
            
            # Generate UUID for user
            user_id = str(uuid.uuid4())
            
            # Insert user
            query = """
            INSERT INTO users (users_id, email, username, password_hash, first_name, last_name, 
                             phone, department, employee_id, `group`)
            VALUES (:users_id, :email, :username, :password_hash, :first_name, :last_name, 
                    :phone, :department, :employee_id, :group)
            """
            
            values = {
                "users_id": user_id,
                "email": email,
                "username": username,
                "password_hash": password_hash,
                "first_name": first_name,
                "last_name": last_name,
                "phone": phone,
                "department": department,
                "employee_id": employee_id,
                "group": group
            }
            
            await db_manager.execute(query, values)
            
            # Assign default Employee role
            await self._assign_default_role(user_id)
            
            # Fetch and return the created user
            return await self.get_user_by_id(user_id)
            
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise
    
    async def _assign_default_role(self, user_id: str) -> None:
        """Assign default Employee role to new user."""
        try:
            # Get Employee role ID
            role_query = "SELECT roles_id FROM roles WHERE name = 'Employee' AND is_active = TRUE"
            role_result = await db_manager.fetch_one(role_query)
            
            if role_result:
                # Assign role to user
                assignment_query = """
                INSERT INTO user_roles (user_roles_id, users_id, roles_id)
                VALUES (:user_roles_id, :users_id, :roles_id)
                """
                
                values = {
                    "user_roles_id": str(uuid.uuid4()),
                    "users_id": user_id,
                    "roles_id": role_result["roles_id"]
                }
                
                await db_manager.execute(assignment_query, values)
        except Exception as e:
            logger.warning(f"Failed to assign default role: {e}")
    
    async def get_user_by_email_or_username(self, email: str, username: str) -> Optional[Dict[str, Any]]:
        """Get user by email or username."""
        query = """
        SELECT users_id, email, username, password_hash, first_name, last_name, 
               phone, department, employee_id, `group`, is_active, created_at, updated_at
        FROM users 
        WHERE (email = :email OR username = :username) AND is_active = TRUE
        """
        
        values = {"email": email, "username": username}
        return await db_manager.fetch_one(query, values)
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID with role information."""
        # query = """
        # SELECT u.users_id, u.email, u.username, u.first_name, u.last_name, 
        #        u.phone, u.department, u.employee_id, u.`group`, u.is_active, 
        #        u.created_at, u.updated_at,
        #        GROUP_CONCAT(r.name) as roles,
        #        CASE WHEN GROUP_CONCAT(r.name) LIKE '%Admin%' THEN TRUE ELSE FALSE END as is_admin
        # FROM users u
        # LEFT JOIN user_roles ur ON u.users_id = ur.users_id AND ur.is_active = TRUE
        # LEFT JOIN roles r ON ur.roles_id = r.roles_id AND r.is_active = TRUE
        # WHERE u.users_id = :user_id AND u.is_active = TRUE
        # GROUP BY u.users_id
        # """
        
        
        query = """
        SELECT u.users_id, u.email, u.username, u.first_name, u.last_name, 
               u.phone, u.department, u.employee_id, u.is_active, 
               u.created_at, u.updated_at,
               r.name as roles
        FROM users u
        Inner JOIN user_roles ur ON u.users_id = ur.users_id
        Inner JOIN roles r ON ur.roles_id = r.roles_id 
        WHERE u.users_id = :user_id AND u.is_active = TRUE;
        
        """
        
        values = {"user_id": user_id}
        return await db_manager.fetch_one(query, values)
    
    async def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with username/password."""
        query = """
        SELECT u.users_id, u.email, u.username, u.password_hash, u.first_name, u.last_name, 
               u.phone, u.department, u.employee_id, u.`group`, u.is_active, 
               u.created_at, u.updated_at,
               GROUP_CONCAT(r.name) as roles,
               CASE WHEN GROUP_CONCAT(r.name) LIKE '%Admin%' THEN TRUE ELSE FALSE END as is_admin
        FROM users u
        LEFT JOIN user_roles ur ON u.users_id = ur.users_id AND ur.is_active = TRUE
        LEFT JOIN roles r ON ur.roles_id = r.roles_id AND r.is_active = TRUE
        WHERE (u.username = :username OR u.email = :username) AND u.is_active = TRUE
        GROUP BY u.users_id
        """
        
        values = {"username": username}
        user = await db_manager.fetch_one(query, values)
        
        if not user:
            return None
        
        # password = hash_password(password)
        
        # print(password)
        # print(user["password_hash"])
        if not verify_password(password, user["password_hash"]):
            return None
        
        # Update last login
        await self._update_last_login(user["users_id"])
        
        return user
    
    async def _update_last_login(self, user_id: str) -> None:
        """Update user's last login timestamp."""
        try:
            query = "UPDATE users SET last_login = NOW() WHERE users_id = :user_id"
            await db_manager.execute(query, {"user_id": user_id})
        except Exception as e:
            logger.warning(f"Failed to update last login: {e}")
    
    async def create_tokens(self, user: Dict[str, Any]) -> Dict[str, Any]:
        """Create access and refresh tokens for user."""
        # Create access token
        access_token_data = {
            "sub": user["users_id"],
            "username": user["username"],
            "email": user["email"],
            "is_admin": user.get("is_admin", False),
            "roles": user.get("roles", "")
        }
        
        access_token = create_access_token(access_token_data)
        
        # Create refresh token
        refresh_token_data = {"sub": user["users_id"]}
        refresh_token = create_refresh_token(refresh_token_data)
        
        # Store refresh token hash in database
        await self.store_refresh_token(user["users_id"], refresh_token)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_days
        }
    
    async def store_refresh_token(self, user_id: str, refresh_token: str) -> None:
        """Store refresh token hash in database."""
        # Create hash of refresh token for storage
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        
        # Calculate expiration
        expires_at = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
        
        query = """
        INSERT INTO refresh_tokens (user_id, token_hash, expires_at)
        VALUES (:user_id, :token_hash, :expires_at)
        """
        
        values = {
            "user_id": user_id,
            "token_hash": token_hash,
            "expires_at": expires_at
        }
        
        await db_manager.execute(query, values)
    
    async def verify_refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Verify refresh token and return user if valid."""
        # Verify JWT structure first
        payload = verify_token(refresh_token, "refresh")
        if not payload:
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        # Check if token exists in database and is not revoked
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        
        query = """
        SELECT rt.id, rt.user_id, rt.expires_at, rt.is_revoked,
               u.users_id, u.email, u.username, u.first_name, u.last_name, 
               u.phone, u.department, u.employee_id, u.`group`, u.is_active, 
               u.created_at, u.updated_at,
               GROUP_CONCAT(r.name) as roles,
               CASE WHEN GROUP_CONCAT(r.name) LIKE '%Admin%' THEN TRUE ELSE FALSE END as is_admin
        FROM refresh_tokens rt
        JOIN users u ON rt.user_id = u.users_id
        LEFT JOIN user_roles ur ON u.users_id = ur.users_id AND ur.is_active = TRUE
        LEFT JOIN roles r ON ur.roles_id = r.roles_id AND r.is_active = TRUE
        WHERE rt.token_hash = :token_hash 
        AND rt.user_id = :user_id 
        AND rt.is_revoked = FALSE
        AND rt.expires_at > NOW()
        AND u.is_active = TRUE
        GROUP BY u.users_id
        """
        
        values = {
            "token_hash": token_hash,
            "user_id": user_id
        }
        
        result = await db_manager.fetch_one(query, values)
        
        if not result:
            return None
        
        # Return user data
        return {
            "users_id": result["users_id"],
            "email": result["email"],
            "username": result["username"],
            "first_name": result["first_name"],
            "last_name": result["last_name"],
            "phone": result["phone"],
            "department": result["department"],
            "employee_id": result["employee_id"],
            "group": result["group"],
            "is_active": result["is_active"],
            "created_at": result["created_at"],
            "updated_at": result["updated_at"],
            "roles": result["roles"],
            "is_admin": result["is_admin"]
        }
    
    async def revoke_refresh_token(self, refresh_token: str) -> bool:
        """Revoke a refresh token."""
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        
        query = """
        UPDATE refresh_tokens 
        SET is_revoked = TRUE 
        WHERE token_hash = :token_hash
        """
        
        values = {"token_hash": token_hash}
        result = await db_manager.execute(query, values)
        
        return result > 0
    
    async def revoke_all_user_tokens(self, user_id: str) -> None:
        """Revoke all refresh tokens for a user."""
        query = """
        UPDATE refresh_tokens 
        SET is_revoked = TRUE 
        WHERE user_id = :user_id AND is_revoked = FALSE
        """
        
        values = {"user_id": user_id}
        await db_manager.execute(query, values)
    
    async def change_password(self, user_id: str, current_password: str, new_password: str) -> bool:
        """Change user password after verifying current password."""
        # Get current user
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        
        # Get password hash
        password_query = "SELECT password_hash FROM users WHERE users_id = :user_id"
        password_result = await db_manager.fetch_one(password_query, {"user_id": user_id})
        
        if not password_result:
            return False
        
        # Verify current password
        if not verify_password(current_password, password_result["password_hash"]):
            return False
        
        # Hash new password
        new_password_hash = hash_password(new_password)
        
        # Update password
        query = """
        UPDATE users 
        SET password_hash = :password_hash, updated_at = NOW()
        WHERE users_id = :user_id
        """
        
        values = {
            "password_hash": new_password_hash,
            "user_id": user_id
        }
        
        result = await db_manager.execute(query, values)
        
        if result > 0:
            # Revoke all existing refresh tokens to force re-login
            await self.revoke_all_user_tokens(user_id)
            return True
        
        return False
    
    async def authenticate_with_azure(self, id_token: str) -> Dict[str, Any]:
        """
        Verify Azure ID token (from MSAL in frontend), auto-provision local user if necessary,
        and issue local app tokens.
        """
        payload = await verify_azure_token(id_token)

        email = payload.get("email") or payload.get("preferred_username")
        first_name = payload.get("given_name", "") or payload.get("name", "").split(" ")[0] if payload.get("name") else ""
        last_name = payload.get("family_name", "")

        if not email:
            raise HTTPException(status_code=400, detail="Azure token missing email")

        # Check for existing user (by email or username)
        existing = await self.get_user_by_email_or_username(email, email)
        if not existing:
            # Create user with random password (not used)
            user = await self.create_user(
                email=email,
                username=email,
                # password=str("Password@123"),
                password=str(uuid.uuid4()),
                first_name=first_name,
                last_name=last_name,
            )
        else:
            user = existing

        await self._update_last_login(user["users_id"])
        return await self.create_tokens(user)

    async def authenticate_with_azure_code(self, code: str) -> Dict[str, Any]:
        """
        Redirect-based OAuth2 login:
        Exchange auth code for tokens, verify ID token, create/get user, and return app tokens.
        """
        token_url = settings.azure_ad_token_url

        data = {
            "client_id": settings.azure_ad_client_id,
            "client_secret": settings.azure_ad_client_secret,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.azure_ad_redirect_uri,
            "scope": settings.azure_ad_scope,
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(token_url, data=data, timeout=10.0)
        if resp.status_code != 200:
            detail = f"Azure token exchange failed: {resp.status_code} {resp.text}"
            logger.error(detail)
            raise HTTPException(status_code=400, detail=detail)

        token_data = resp.json()
        id_token = token_data.get("id_token")
        if not id_token:
            raise HTTPException(status_code=400, detail="Azure did not return ID token")

        # Verify ID token using the helper (uses JWKS)
        payload = await verify_azure_token(id_token)

        # Extract user info
        email = payload.get("email") or payload.get("preferred_username")
        name = payload.get("name", "")
        first_name = payload.get("given_name", "") or (name.split(" ")[0] if name else "")
        last_name = payload.get("family_name", "") or (name.split(" ")[1] if " " in name else "")

        if not email:
            raise HTTPException(status_code=400, detail="Email not found in Azure token")

        existing = await self.get_user_by_email_or_username(email, email)
        if not existing:
            user = await self.create_user(
                email=email,
                username=email,
                password=str(uuid.uuid4()),
                first_name=first_name,
                last_name=last_name,
            )
            users_id = user["users_id"]
        else:
            user = existing

        print(user)
        
        await self._update_last_login(user["users_id"])
        tokens = await self.create_tokens(user)
        return tokens


# Global instance
auth_service = AuthService()