"""
FastAPI Dependencies for Authentication & Authorization.

These dependencies are used in route definitions to protect endpoints.

Usage:
    @router.get("/protected")
    def protected_route(user: UserProfile = Depends(get_current_user)):
        return user

    @router.post("/admin-only")
    def admin_route(user: UserProfile = Depends(require_role(UserRole.ADMIN))):
        return {"status": "admin access granted"}
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

from app.auth.jwt_handler import decode_access_token
from app.auth.schemas import UserProfile
from app.auth.roles import UserRole, is_role_at_least

# Standard FastAPI Bearer token scheme
security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserProfile:
    """
    Extract and verify the JWT from the Authorization header.
    Returns the user profile if valid, raises HTTPException otherwise.
    """
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        role = payload.get("role", "user")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        return UserProfile(
            id=user_id,
            email=payload.get("email", ""),  # Supabase tokens might not include email by default, handled in service
            role=role
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def require_role(minimum_role: UserRole):
    """
    Dependency factory to check if the current user meets the minimum role requirement.
    
    Args:
        minimum_role: The lowest role allowed to access the endpoint.
        
    Returns:
        A FastAPI dependency function.
    """
    def role_checker(current_user: UserProfile = Depends(get_current_user)) -> UserProfile:
        if not is_role_at_least(current_user.role, minimum_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Minimum role required: {minimum_role.value}"
            )
        return current_user
    
    return role_checker
