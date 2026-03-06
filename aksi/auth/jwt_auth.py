"""
JWT Authentication Module
=========================

JWT-based authentication for AKSI API.
"""

from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import hashlib
import secrets

# Lazy import for jose
_jose = None


def _get_jose():
    """Lazy import python-jose."""
    global _jose
    if _jose is None:
        try:
            from jose import JWTError, jwt
            _jose = (JWTError, jwt)
        except ImportError:
            _jose = (None, None)
    return _jose


from aksi.config import settings


class TokenData(BaseModel):
    """JWT token payload data."""

    username: Optional[str] = None
    user_id: Optional[str] = None
    roles: list = []
    exp: Optional[datetime] = None


class User(BaseModel):
    """User model."""

    user_id: str
    username: str
    email: Optional[str] = None
    roles: list = []
    is_active: bool = True
    created_at: Optional[datetime] = None


class Token(BaseModel):
    """Token response model."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class JWTAuth:
    """
    JWT Authentication handler.

    Provides token creation, verification, and user management.
    """

    def __init__(
        self,
        secret_key: Optional[str] = None,
        algorithm: Optional[str] = None,
        access_token_expire_minutes: Optional[int] = None
    ):
        """
        Initialize JWT auth handler.

        Args:
            secret_key: Secret key for signing tokens
            algorithm: JWT algorithm (default: HS256)
            access_token_expire_minutes: Token expiration time in minutes
        """
        self.secret_key = secret_key or settings.jwt_secret_key
        self.algorithm = algorithm or settings.jwt_algorithm
        self.access_token_expire_minutes = (
            access_token_expire_minutes or
            settings.jwt_access_token_expire_minutes
        )
        self._users_db = {}  # In-memory user storage (replace with DB in production)

    def create_access_token(
        self,
        data: dict,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create JWT access token.

        Args:
            data: Payload data to encode
            expires_delta: Optional custom expiration time

        Returns:
            Encoded JWT token string
        """
        JWTError, jwt = _get_jose()

        if jwt is None:
            raise RuntimeError("python-jose not installed. Install with: pip install python-jose[cryptography]")

        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)

        to_encode.update({"exp": expire})

        encoded_jwt = jwt.encode(
            to_encode,
            self.secret_key,
            algorithm=self.algorithm
        )
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[TokenData]:
        """
        Verify and decode JWT token.

        Args:
            token: JWT token string

        Returns:
            TokenData if valid, None otherwise
        """
        JWTError, jwt = _get_jose()

        if jwt is None:
            return None

        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )

            username: str = payload.get("sub")
            user_id: str = payload.get("user_id")
            roles: list = payload.get("roles", [])
            exp = payload.get("exp")

            if username is None:
                return None

            return TokenData(
                username=username,
                user_id=user_id,
                roles=roles,
                exp=datetime.fromtimestamp(exp) if exp else None
            )
        except JWTError:
            return None

    def hash_password(self, password: str) -> str:
        """
        Hash password using SHA-256.

        In production, use bcrypt or argon2.

        Args:
            password: Plain text password

        Returns:
            Hashed password
        """
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify password against hash.

        Args:
            plain_password: Plain text password
            hashed_password: Hashed password to verify against

        Returns:
            True if password matches
        """
        return self.hash_password(plain_password) == hashed_password

    def register_user(
        self,
        username: str,
        password: str,
        email: Optional[str] = None,
        roles: list = None
    ) -> Optional[User]:
        """
        Register a new user.

        Args:
            username: Username
            password: Plain text password
            email: User email
            roles: List of role names

        Returns:
            User object if successful, None if username exists
        """
        if username in self._users_db:
            return None

        user_id = secrets.token_hex(8)
        hashed_password = self.hash_password(password)

        user_data = {
            "user_id": user_id,
            "username": username,
            "password_hash": hashed_password,
            "email": email,
            "roles": roles or ["user"],
            "is_active": True,
            "created_at": datetime.utcnow()
        }

        self._users_db[username] = user_data

        return User(
            user_id=user_id,
            username=username,
            email=email,
            roles=user_data["roles"],
            is_active=True,
            created_at=user_data["created_at"]
        )

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate user with username and password.

        Args:
            username: Username
            password: Plain text password

        Returns:
            User object if authenticated, None otherwise
        """
        user_data = self._users_db.get(username)

        if not user_data:
            return None

        if not self.verify_password(password, user_data["password_hash"]):
            return None

        if not user_data.get("is_active", True):
            return None

        return User(
            user_id=user_data["user_id"],
            username=user_data["username"],
            email=user_data.get("email"),
            roles=user_data.get("roles", []),
            is_active=user_data.get("is_active", True),
            created_at=user_data.get("created_at")
        )

    def get_user(self, username: str) -> Optional[User]:
        """
        Get user by username.

        Args:
            username: Username

        Returns:
            User object if found
        """
        user_data = self._users_db.get(username)

        if not user_data:
            return None

        return User(
            user_id=user_data["user_id"],
            username=user_data["username"],
            email=user_data.get("email"),
            roles=user_data.get("roles", []),
            is_active=user_data.get("is_active", True),
            created_at=user_data.get("created_at")
        )

    def login(self, username: str, password: str) -> Optional[Token]:
        """
        Login user and return access token.

        Args:
            username: Username
            password: Plain text password

        Returns:
            Token object if successful, None otherwise
        """
        user = self.authenticate_user(username, password)

        if not user:
            return None

        access_token = self.create_access_token(
            data={
                "sub": user.username,
                "user_id": user.user_id,
                "roles": user.roles
            }
        )

        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=self.access_token_expire_minutes * 60
        )


# Global auth instance
_jwt_auth = JWTAuth()

# HTTP Bearer security scheme
security = HTTPBearer(auto_error=False)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create access token using global auth instance."""
    return _jwt_auth.create_access_token(data, expires_delta)


def verify_token(token: str) -> Optional[TokenData]:
    """Verify token using global auth instance."""
    return _jwt_auth.verify_token(token)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Optional[TokenData]:
    """
    FastAPI dependency to get current user from JWT token.

    Usage:
        @app.get("/protected")
        async def protected_route(user: TokenData = Depends(get_current_user)):
            return {"user": user.username}
    """
    if credentials is None:
        return None

    token_data = verify_token(credentials.credentials)

    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return token_data


async def require_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    """
    FastAPI dependency that requires authentication.

    Raises 401 if no valid token provided.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token_data = verify_token(credentials.credentials)

    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return token_data


def require_role(required_roles: list):
    """
    FastAPI dependency factory for role-based authorization.

    Usage:
        @app.get("/admin")
        async def admin_route(user: TokenData = Depends(require_role(["admin"]))):
            return {"admin": True}
    """
    async def role_checker(
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> TokenData:
        if credentials is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"}
            )

        token_data = verify_token(credentials.credentials)

        if token_data is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"}
            )

        # Check if user has any of the required roles
        user_roles = set(token_data.roles)
        required_roles_set = set(required_roles)

        if not user_roles.intersection(required_roles_set):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )

        return token_data

    return role_checker
