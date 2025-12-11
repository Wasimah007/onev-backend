"""
Password hashing and verification utilities using bcrypt.
"""

from passlib.context import CryptContext
from app.config import settings
import bcrypt


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))





# Create password context with bcrypt
# pwd_context = CryptContext(
#     schemes=["bcrypt"],
#     deprecated="auto",
#     bcrypt__rounds=settings.bcrypt_rounds
# )


# def hash_password(password: str) -> str:
#     """Hash a password using bcrypt."""
#     return pwd_context.hash(password)


# def verify_password(plain_password: str, hashed_password: str) -> bool:
#     """Verify a password against its hash."""
#     return pwd_context.verify(plain_password, hashed_password)