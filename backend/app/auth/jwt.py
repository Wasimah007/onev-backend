"""
JWT token creation and verification utilities.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from app.config import settings

logger = logging.getLogger(__name__)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.access_token_expire_days)
    
    to_encode.update({"exp": expire, "type": "access"})
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.jwt_secret_key, 
        algorithm=settings.jwt_algorithm
    )
    
    print(encoded_jwt)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    
    to_encode.update({"exp": expire, "type": "refresh"})
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.jwt_secret_key, 
        algorithm=settings.jwt_algorithm
    )
    
    return encoded_jwt


def verify_token(token: str, expected_type: str = "access") -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string
        expected_type: Expected token type ("access" or "refresh")
    
    Returns:
        Token payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token, 
            settings.jwt_secret_key, 
            algorithms=[settings.jwt_algorithm]
        )
        
        # Check token type
        token_type = payload.get("type")
        if token_type != expected_type:
            logger.warning(f"Token type mismatch. Expected: {expected_type}, Got: {token_type}")
            return None
        
        # Check expiration
        exp = payload.get("exp")
        if exp is None:
            logger.warning("Token missing expiration")
            return None
        
        if datetime.utcnow() > datetime.fromtimestamp(exp):
            logger.warning("Token has expired")
            return None
        
        return payload
        
    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during token verification: {e}")
        return None


def get_token_subject(token: str) -> Optional[str]:
    """Extract subject (usually user ID) from token."""
    payload = verify_token(token)
    if payload:
        return payload.get("sub")
    return None