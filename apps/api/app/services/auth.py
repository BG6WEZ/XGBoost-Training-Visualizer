"""
认证服务

P1-T15: 简化登录与用户管理
提供密码哈希、JWT token 生成和验证功能，Token 黑名单管理

性能优化 (M7-T95):
- bcrypt 是 CPU 密集型操作，使用 ThreadPoolExecutor 避免阻塞事件循环
"""
import logging
import os
import secrets
import string
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import jwt, JWTError

from app.config import settings

ALGORITHM = "HS256"
logger = logging.getLogger(__name__)

# Thread pool for CPU-bound bcrypt operations
_executor = ThreadPoolExecutor(max_workers=4)


def hash_password(password: str) -> str:
    """哈希密码（同步，用于初始化）"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码（同步，用于初始化）"""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False


async def verify_password_async(plain_password: str, hashed_password: str) -> bool:
    """异步验证密码，使用线程池避免阻塞事件循环"""
    import asyncio
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        _executor,
        bcrypt.checkpw,
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


class TokenBlacklist:
    """Token 黑名单管理（支持 Redis + 降级）"""

    def __init__(self):
        self.redis_client = None
        self._try_init_redis()

    def _try_init_redis(self):
        """尝试连接 Redis，失败则记录 warning，不影响启动"""
        try:
            import redis
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            self.redis_client.ping()
            logger.info("✓ Redis 连接成功，Token 黑名单已启用")
        except Exception as e:
            logger.warning(f"⚠ Redis 不可用，将降级为无黑名单检查: {e}")
            self.redis_client = None

    def revoke_token(self, jti: str, exp_timestamp: int) -> bool:
        """将 JTI 写入黑名单，TTL = token 剩余有效期"""
        if not self.redis_client:
            return True  # 降级
        try:
            now = int(datetime.now(timezone.utc).timestamp())
            ttl_seconds = max(1, exp_timestamp - now)
            key = f"blacklist:{jti}"
            self.redis_client.setex(key, ttl_seconds, "revoked")
            logger.debug(f"✓ Token {jti} 已加入黑名单（TTL: {ttl_seconds}s）")
            return True
        except Exception as e:
            logger.error(f"✗ 黑名单写入失败: {e}")
            return False

    def is_token_revoked(self, jti: str) -> bool:
        """检查 JTI 是否在黑名单中"""
        if not self.redis_client:
            return False  # 降级
        try:
            key = f"blacklist:{jti}"
            exists = self.redis_client.exists(key)
            return bool(exists)
        except Exception as e:
            logger.warning(f"⚠ 黑名单检查失败，降级为允许: {e}")
            return False


# 全局黑名单实例
token_blacklist = TokenBlacklist()


def create_access_token(data: dict[str, object], expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌，自动注入 JTI claim"""
    to_encode = data.copy()
    # 自动注入 JTI（JWT ID，用于黑名单检查）
    to_encode["jti"] = str(uuid.uuid4())
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict[str, object]]:
    """解码访问令牌"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def revoke_token(token: str) -> bool:
    """吊销一个 token"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])
        jti = payload.get("jti")
        exp = payload.get("exp")

        if not jti:
            raise ValueError("Token 中缺少 JTI claim，无法吊销")

        # exp 可能是 datetime 对象或 int
        if isinstance(exp, datetime):
            exp_timestamp = int(exp.timestamp())
        elif isinstance(exp, (int, float)):
            exp_timestamp = int(exp)
        else:
            # 如果没有 exp，使用一个默认 TTL
            exp_timestamp = int(datetime.now(timezone.utc).timestamp()) + 3600

        success = token_blacklist.revoke_token(jti, exp_timestamp)
        if not success:
            logger.error("⚠ 黑名单写入失败，但不中断登出流程")
        return True
    except JWTError:
        logger.warning("Token 格式错误，无法吊销")
        return False


def generate_random_password(length: int = 12) -> str:
    """生成随机密码"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))
