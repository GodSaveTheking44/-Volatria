import hashlib
import jwt
from datetime import datetime, timedelta
from typing import Optional, List
from backend.core.config import settings
from backend.core.exceptions import SecurityException

# Standard hashing using SHA256 and a fixed salt for out-of-the-box compatibility
SALT = "volatria_salt_2026"

def hash_password(password: str) -> str:
    pwd_bytes = (password + SALT).encode('utf-8')
    return hashlib.sha256(pwd_bytes).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hash_password(plain_password) == hashed_password

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.PyJWTError:
        raise SecurityException("Invalid signature or expired token")

class RBACRole:
    RESEARCHER = "Researcher"
    TRADER = "Trader"
    RISK_MANAGER = "Risk Manager"
    ADMINISTRATOR = "Administrator"

def verify_role_access(user_role: str, allowed_roles: List[str]):
    if user_role not in allowed_roles:
        raise SecurityException("Insufficient permissions for this action")
