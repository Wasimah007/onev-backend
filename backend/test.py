# from passlib.context import CryptContext
# from app.config import settings
# import bcrypt


# def hash_password(password: str) -> str:
    
#     print(bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'))
    
    
# hash_password("admin123")


# def verify_password(plain_password: str, hashed_password: str) -> bool:
#     print(bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8')))

# verify_password("admin123","$2b$12$A5L2bxUgsibwWFcYCdRs3OytbMCI8bDmJWD4SMg75VMFHtI4d18Dq")

from app.auth import router as auth_router
print(type(auth_router.router))