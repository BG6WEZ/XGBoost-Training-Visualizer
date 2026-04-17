"""
认证路由

P1-T15: 简化登录与用户管理
提供登录、登出、获取当前用户信息、修改密码等接口
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import uuid

from app.database import get_db
from app.models import User, UserRole, UserStatus
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    UserResponse,
    PasswordChangeRequest,
)
from app.services.auth import (
    hash_password,
    verify_password,
    verify_password_async,
    create_access_token,
    decode_access_token,
    revoke_token,
    token_blacklist,
)

router = APIRouter()
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """获取当前登录用户（含黑名单检查）"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证令牌"
        )
    
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌"
        )
    
    # 黑名单检查
    jti = payload.get("jti")
    if jti and token_blacklist.is_token_revoked(str(jti)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 已被吊销，请重新登录"
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的令牌内容"
        )
    
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的用户 ID"
        )
    
    result = await db.execute(
        select(User).where(User.id == user_uuid)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在"
        )
    
    if user.status == UserStatus.disabled.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )
    
    return user


async def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前管理员用户"""
    if current_user.role != UserRole.admin.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


@router.post("/auth/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    用户登录
    
    验证用户名和密码，返回访问令牌
    
    性能优化 (M7-T101):
    - 移除 last_login_at 的同步 commit，减少响应延迟
    """
    result = await db.execute(
        select(User).where(User.username == request.username)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    if user.status == UserStatus.disabled.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )
    
    if not await verify_password_async(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    # 性能优化：跳过 last_login_at 更新，避免阻塞响应
    # user.last_login_at = datetime.utcnow()
    # await db.commit()
    
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=str(user.id),
            username=user.username,
            role=user.role,
            status=user.status,
            must_change_password=user.must_change_password or False,
            created_at=user.created_at,
            last_login_at=user.last_login_at,
        )
    )


@router.post("/auth/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: User = Depends(get_current_user),
):
    """
    用户登出
    
    吊销当前 token，使其无法继续使用
    Redis 不可用时降级为无黑名单检查
    """
    token = credentials.credentials
    try:
        revoke_token(token)
    except Exception:
        # 吊销失败也不影响登出流程
        pass
    return {"message": "登出成功"}


@router.get("/auth/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user)
):
    """
    获取当前用户信息
    """
    return UserResponse(
        id=str(current_user.id),
        username=current_user.username,
        role=current_user.role,
        status=current_user.status,
        must_change_password=current_user.must_change_password or False,
        created_at=current_user.created_at,
        last_login_at=current_user.last_login_at,
    )


@router.post("/auth/change-password")
async def change_password(
    request: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    修改密码
    """
    if not verify_password(request.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="原密码错误"
        )
    
    current_user.password_hash = hash_password(request.new_password)
    current_user.must_change_password = False
    await db.commit()
    
    return {"message": "密码修改成功"}
