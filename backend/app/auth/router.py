"""
Authentication routes for registration, login, token refresh, logout, and Azure AD SSO.
"""

import logging
import urllib.parse
from fastapi import (
    APIRouter, HTTPException, Depends, status, Request
)
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel
from typing import Dict, Any

from app.auth.service import auth_service
from app.auth.jwt import verify_token
from app.config import settings
from app.auth.schemas import (
    UserRegister, UserLogin, TokenResponse, RefreshTokenRequest,
    AccessTokenResponse, UserProfile, ChangePassword, MessageResponse
)
from app.auth.dependencies import get_current_user, oauth2_scheme
from fastapi.security import HTTPBearer , HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication & Azure AD"])


# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

oauth2_scheme = HTTPBearer()

# ------------------------------
# JWT Auth: Current User Helpers
# ------------------------------


async def get_current_user(token: HTTPAuthorizationCredentials = Depends(oauth2_scheme)) -> Dict[str, Any]:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token_str = token.credentials  # Extract the token from "Bearer <token>"

    payload = verify_token(token_str, "access")
    if payload is None:
        raise credentials_exception

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    user = await auth_service.get_user_by_id(user_id)
    if user is None:
        raise credentials_exception

    return user
# async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Could not validate credentials",
#         headers={"WWW-Authenticate": "Bearer"},
#     )
#     payload = verify_token(token, "access")
#     if payload is None:
#         raise credentials_exception

#     user_id = payload.get("sub")
#     if user_id is None:
#         raise credentials_exception

#     user = await auth_service.get_user_by_id(user_id)
#     if user is None:
#         raise credentials_exception

#     return user


async def get_current_admin_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

async def get_current_admin_user(current_user: Dict[str, Any] = Depends(get_current_user)):
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


# ------------------------------
# Regular JWT Auth Routes
# ------------------------------
@router.post("/register", response_model=UserProfile, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister):
    user = await auth_service.create_user(
        email=user_data.email,
        username=user_data.username,
        password=user_data.password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
    )
    if user is None:
        raise HTTPException(status_code=400, detail="User already exists")

    return UserProfile(**user)


@router.post("/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await auth_service.authenticate_user(form_data.username, form_data.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    tokens = await auth_service.create_tokens(user)
    return TokenResponse(**tokens)


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh_token(refresh_data: RefreshTokenRequest):
    user = await auth_service.verify_refresh_token(refresh_data.refresh_token)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    from app.auth.jwt import create_access_token
    access_token = create_access_token({
        "sub": user["users_id"],
        "username": user["username"],
        "email": user["email"],
        "is_admin": user.get("is_admin", False),
        "roles": user.get("roles", "")
    })

    return AccessTokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    refresh_data: RefreshTokenRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    success = await auth_service.revoke_refresh_token(refresh_data.refresh_token)
    if not success:
        raise HTTPException(status_code=400, detail="Invalid refresh token")

    return MessageResponse(message="Successfully logged out")


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    return UserProfile(**current_user)


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    password_data: ChangePassword,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    success = await auth_service.change_password(
        user_id=current_user["users_id"],
        current_password=password_data.current_password,
        new_password=password_data.new_password
    )
    if not success:
        raise HTTPException(status_code=400, detail="Incorrect current password")

    return MessageResponse(message="Password changed successfully. Please re-login.")


# ------------------------------
# Azure AD Login (SSO)
# ------------------------------
class AzureLoginRequest(BaseModel):
    id_token: str


@router.post("/azure/login")
async def azure_login(req: AzureLoginRequest):
    """Login using Azure AD ID token (for MSAL or SPA clients)."""
    try:
        tokens = await auth_service.authenticate_with_azure(req.id_token)
        return tokens
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/azure/authorize")
async def azure_authorize():
    """Redirect user to Microsoft Login page."""
    params = {
        "client_id": settings.azure_ad_client_id,
        "response_type": "code",
        "redirect_uri": settings.azure_ad_redirect_uri,
        "response_mode": "query",
        "scope": "openid profile email"
    }
    url = (
        f"https://login.microsoftonline.com/"
        f"{settings.azure_ad_tenant_id}/oauth2/v2.0/authorize?"
        f"{urllib.parse.urlencode(params)}"
    )
    return RedirectResponse(url)


@router.get("/azure/callback/")
async def azure_callback(code: str = None):
    """Callback endpoint for Azure OAuth2 (redirect-based login)."""
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")

    tokens = await auth_service.authenticate_with_azure_code(code)
    return JSONResponse(tokens)
