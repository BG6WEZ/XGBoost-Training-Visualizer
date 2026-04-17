"""
认证相关 Schema

P1-T15: 简化登录与用户管理
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    """登录响应"""
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class UserResponse(BaseModel):
    """用户信息响应"""
    id: str
    username: str
    role: str
    status: str
    must_change_password: bool = False
    created_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserCreateRequest(BaseModel):
    """创建用户请求（管理员）"""
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=6)
    role: str = Field(default="user", pattern="^(admin|user)$")


class UserUpdateRequest(BaseModel):
    """更新用户请求（管理员）"""
    status: Optional[str] = Field(None, pattern="^(active|disabled)$")
    role: Optional[str] = Field(None, pattern="^(admin|user)$")


class PasswordChangeRequest(BaseModel):
    """修改密码请求"""
    old_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=6)


class PasswordResetRequest(BaseModel):
    """重置密码请求（管理员）"""
    new_password: str = Field(..., min_length=6)


class UserListResponse(BaseModel):
    """用户列表响应"""
    users: list[UserResponse]
    total: int
