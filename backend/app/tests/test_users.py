"""
Tests for user management endpoints.
"""

import pytest
from httpx import AsyncClient
from app.tests.test_auth import client, setup_database, test_user_data, registered_user


class TestUsers:
    """Test user management endpoints."""
    
    async def get_admin_token(self, client: AsyncClient):
        """Helper to get admin token."""
        # Login as admin (created in schema.sql)
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response = await client.post(
            "/api/v1/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code == 200:
            return response.json()["access_token"]
        return None
    
    async def get_user_token(self, client: AsyncClient, test_user_data, registered_user):
        """Helper to get regular user token."""
        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        }
        
        response = await client.post(
            "/api/v1/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        return response.json()["access_token"]
    
    async def test_create_user_as_admin(self, client: AsyncClient):
        """Test creating user as admin."""
        admin_token = await self.get_admin_token(client)
        if not admin_token:
            pytest.skip("Admin user not available")
        
        user_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "newpassword123",
            "first_name": "New",
            "last_name": "User",
            "is_admin": False
        }
        
        response = await client.post(
            "/api/v1/users/",
            json=user_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["username"] == user_data["username"]
        assert "password" not in data
    
    async def test_create_user_as_regular_user(self, client: AsyncClient, test_user_data, registered_user):
        """Test creating user as regular user (should fail)."""
        user_token = await self.get_user_token(client, test_user_data, registered_user)
        
        user_data = {
            "email": "forbidden@example.com",
            "username": "forbidden",
            "password": "password123",
            "first_name": "Forbidden",
            "last_name": "User",
            "is_admin": False
        }
        
        response = await client.post(
            "/api/v1/users/",
            json=user_data,
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 403
    
    async def test_get_users_list(self, client: AsyncClient, test_user_data, registered_user):
        """Test getting users list."""
        user_token = await self.get_user_token(client, test_user_data, registered_user)
        
        response = await client.get(
            "/api/v1/users/",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert isinstance(data["users"], list)
    
    async def test_get_user_by_id(self, client: AsyncClient, test_user_data, registered_user):
        """Test getting user by ID."""
        user_token = await self.get_user_token(client, test_user_data, registered_user)
        user_id = registered_user["id"]
        
        response = await client.get(
            f"/api/v1/users/{user_id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_id
        assert data["email"] == test_user_data["email"]
    
    async def test_get_other_user_as_regular_user(self, client: AsyncClient, test_user_data, registered_user):
        """Test getting other user as regular user (should fail)."""
        user_token = await self.get_user_token(client, test_user_data, registered_user)
        other_user_id = 999  # Assuming this doesn't exist or is different
        
        response = await client.get(
            f"/api/v1/users/{other_user_id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        # Should be 403 (forbidden) or 404 (not found)
        assert response.status_code in [403, 404]
    
    async def test_update_own_profile(self, client: AsyncClient, test_user_data, registered_user):
        """Test updating own profile."""
        user_token = await self.get_user_token(client, test_user_data, registered_user)
        user_id = registered_user["id"]
        
        update_data = {
            "first_name": "Updated",
            "last_name": "Name"
        }
        
        response = await client.put(
            f"/api/v1/users/{user_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Updated"
        assert data["last_name"] == "Name"
    
    async def test_unauthorized_access(self, client: AsyncClient):
        """Test accessing endpoints without token."""
        response = await client.get("/api/v1/users/")
        assert response.status_code == 401
        
        response = await client.get("/api/v1/users/1")
        assert response.status_code == 401