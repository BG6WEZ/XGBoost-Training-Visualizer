"""
统一存储适配层

支持两种存储模式：
- local: 本地文件系统
- minio: MinIO 对象存储

所有模型文件、预处理输出、特征工程输出都通过此适配层管理。
"""
import os
import logging
import aiofiles
from abc import ABC, abstractmethod
from typing import Optional, BinaryIO, Tuple
from datetime import datetime
import uuid

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class StorageConfig(BaseModel):
    """存储配置"""
    storage_type: str = "local"  # local 或 minio

    # Local 模式配置
    local_base_path: str = "./workspace"

    # MinIO 模式配置
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "xgboost-vis"
    minio_secure: bool = False


class FileInfo(BaseModel):
    """文件信息"""
    storage_type: str
    object_key: str  # 统一使用 object_key，local 模式为相对路径
    full_path: Optional[str] = None  # local 模式下的完整路径
    file_size: int = 0
    content_type: str = "application/octet-stream"
    created_at: Optional[datetime] = None


class StorageAdapter(ABC):
    """存储适配器基类"""

    @abstractmethod
    async def save(self, object_key: str, data: bytes, content_type: str = "application/octet-stream") -> FileInfo:
        """保存文件"""
        pass

    @abstractmethod
    async def save_from_file(self, object_key: str, file_path: str, content_type: str = "application/octet-stream") -> FileInfo:
        """从本地文件保存"""
        pass

    @abstractmethod
    async def read(self, object_key: str) -> bytes:
        """读取文件内容"""
        pass

    @abstractmethod
    async def read_to_file(self, object_key: str, dest_path: str) -> bool:
        """读取文件到本地路径"""
        pass

    @abstractmethod
    async def exists(self, object_key: str) -> bool:
        """检查文件是否存在"""
        pass

    @abstractmethod
    async def delete(self, object_key: str) -> bool:
        """删除文件"""
        pass

    @abstractmethod
    async def get_info(self, object_key: str) -> Optional[FileInfo]:
        """获取文件信息"""
        pass

    @abstractmethod
    async def health_check(self) -> Tuple[bool, str]:
        """健康检查"""
        pass

    @abstractmethod
    def get_full_path(self, object_key: str) -> str:
        """获取文件的完整访问路径"""
        pass


class LocalStorageAdapter(StorageAdapter):
    """本地文件系统存储适配器"""

    def __init__(self, base_path: str = "./workspace"):
        self.base_path = os.path.abspath(base_path)
        os.makedirs(self.base_path, exist_ok=True)
        logger.info(f"LocalStorageAdapter initialized with base_path: {self.base_path}")

    def _get_full_path(self, object_key: str) -> str:
        """获取完整路径"""
        return os.path.join(self.base_path, object_key)

    async def save(self, object_key: str, data: bytes, content_type: str = "application/octet-stream") -> FileInfo:
        """保存文件"""
        full_path = self._get_full_path(object_key)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        async with aiofiles.open(full_path, 'wb') as f:
            await f.write(data)

        file_size = len(data)
        logger.info(f"File saved: {object_key} ({file_size} bytes)")

        return FileInfo(
            storage_type="local",
            object_key=object_key,
            full_path=full_path,
            file_size=file_size,
            content_type=content_type,
            created_at=datetime.utcnow()
        )

    async def save_from_file(self, object_key: str, file_path: str, content_type: str = "application/octet-stream") -> FileInfo:
        """从本地文件保存（复制）"""
        full_path = self._get_full_path(object_key)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        # 读取源文件并写入目标位置
        async with aiofiles.open(file_path, 'rb') as src:
            data = await src.read()

        async with aiofiles.open(full_path, 'wb') as dst:
            await dst.write(data)

        file_size = os.path.getsize(full_path)
        logger.info(f"File copied from {file_path} to {object_key} ({file_size} bytes)")

        return FileInfo(
            storage_type="local",
            object_key=object_key,
            full_path=full_path,
            file_size=file_size,
            content_type=content_type,
            created_at=datetime.utcnow()
        )

    async def read(self, object_key: str) -> bytes:
        """读取文件内容"""
        full_path = self._get_full_path(object_key)

        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found: {object_key}")

        async with aiofiles.open(full_path, 'rb') as f:
            return await f.read()

    async def read_to_file(self, object_key: str, dest_path: str) -> bool:
        """读取文件到本地路径"""
        full_path = self._get_full_path(object_key)

        if not os.path.exists(full_path):
            return False

        os.makedirs(os.path.dirname(dest_path), exist_ok=True)

        async with aiofiles.open(full_path, 'rb') as src:
            data = await src.read()

        async with aiofiles.open(dest_path, 'wb') as dst:
            await dst.write(data)

        return True

    async def exists(self, object_key: str) -> bool:
        """检查文件是否存在"""
        full_path = self._get_full_path(object_key)
        return os.path.exists(full_path)

    async def delete(self, object_key: str) -> bool:
        """删除文件"""
        full_path = self._get_full_path(object_key)

        if os.path.exists(full_path):
            os.remove(full_path)
            logger.info(f"File deleted: {object_key}")
            return True
        return False

    async def get_info(self, object_key: str) -> Optional[FileInfo]:
        """获取文件信息"""
        full_path = self._get_full_path(object_key)

        if not os.path.exists(full_path):
            return None

        stat = os.stat(full_path)
        return FileInfo(
            storage_type="local",
            object_key=object_key,
            full_path=full_path,
            file_size=stat.st_size,
            content_type=self._guess_content_type(object_key),
            created_at=datetime.fromtimestamp(stat.st_ctime)
        )

    async def health_check(self) -> Tuple[bool, str]:
        """健康检查"""
        try:
            if os.path.exists(self.base_path) and os.access(self.base_path, os.W_OK):
                return True, f"Local storage ready at {self.base_path}"
            else:
                return False, f"Local storage not accessible: {self.base_path}"
        except Exception as e:
            return False, f"Local storage error: {str(e)}"

    def get_full_path(self, object_key: str) -> str:
        """获取文件的完整访问路径"""
        return self._get_full_path(object_key)

    def _guess_content_type(self, filename: str) -> str:
        """猜测内容类型"""
        ext = filename.lower().split('.')[-1] if '.' in filename else ''
        content_types = {
            'json': 'application/json',
            'csv': 'text/csv',
            'parquet': 'application/octet-stream',
            'pkl': 'application/octet-stream',
            'model': 'application/octet-stream',
            'ubj': 'application/octet-stream',
        }
        return content_types.get(ext, 'application/octet-stream')


class MinIOStorageAdapter(StorageAdapter):
    """MinIO 对象存储适配器"""

    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        secure: bool = False
    ):
        self.endpoint = endpoint
        self.access_key = access_key
        self.secret_key = secret_key
        self.bucket = bucket
        self.secure = secure
        self._client = None
        self._initialized = False
        logger.info(f"MinIOStorageAdapter configured for {endpoint}/{bucket}")

    def _get_client(self):
        """获取 MinIO 客户端（延迟初始化）"""
        if self._client is None:
            try:
                from minio import Minio
                self._client = Minio(
                    self.endpoint,
                    access_key=self.access_key,
                    secret_key=self.secret_key,
                    secure=self.secure
                )
                # 确保 bucket 存在
                if not self._client.bucket_exists(self.bucket):
                    self._client.make_bucket(self.bucket)
                    logger.info(f"Created MinIO bucket: {self.bucket}")
                self._initialized = True
            except Exception as e:
                logger.error(f"Failed to initialize MinIO client: {e}")
                raise
        return self._client

    async def save(self, object_key: str, data: bytes, content_type: str = "application/octet-stream") -> FileInfo:
        """保存文件到 MinIO"""
        import io

        client = self._get_client()
        data_stream = io.BytesIO(data)

        client.put_object(
            self.bucket,
            object_key,
            data_stream,
            length=len(data),
            content_type=content_type
        )

        logger.info(f"File saved to MinIO: {object_key} ({len(data)} bytes)")

        return FileInfo(
            storage_type="minio",
            object_key=object_key,
            file_size=len(data),
            content_type=content_type,
            created_at=datetime.utcnow()
        )

    async def save_from_file(self, object_key: str, file_path: str, content_type: str = "application/octet-stream") -> FileInfo:
        """从本地文件保存到 MinIO"""
        client = self._get_client()

        file_size = os.path.getsize(file_path)
        client.fput_object(
            self.bucket,
            object_key,
            file_path,
            content_type=content_type
        )

        logger.info(f"File uploaded to MinIO: {object_key} ({file_size} bytes)")

        return FileInfo(
            storage_type="minio",
            object_key=object_key,
            file_size=file_size,
            content_type=content_type,
            created_at=datetime.utcnow()
        )

    async def read(self, object_key: str) -> bytes:
        """从 MinIO 读取文件"""
        client = self._get_client()

        response = None
        try:
            response = client.get_object(self.bucket, object_key)
            return response.read()
        finally:
            if response:
                response.close()
                response.release_conn()

    async def read_to_file(self, object_key: str, dest_path: str) -> bool:
        """从 MinIO 下载文件到本地"""
        client = self._get_client()

        try:
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            client.fget_object(self.bucket, object_key, dest_path)
            return True
        except Exception as e:
            logger.error(f"Failed to download from MinIO: {e}")
            return False

    async def exists(self, object_key: str) -> bool:
        """检查文件是否存在"""
        client = self._get_client()

        try:
            client.stat_object(self.bucket, object_key)
            return True
        except Exception:
            return False

    async def delete(self, object_key: str) -> bool:
        """删除 MinIO 中的文件"""
        client = self._get_client()

        try:
            client.remove_object(self.bucket, object_key)
            logger.info(f"File deleted from MinIO: {object_key}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete from MinIO: {e}")
            return False

    async def get_info(self, object_key: str) -> Optional[FileInfo]:
        """获取文件信息"""
        client = self._get_client()

        try:
            stat = client.stat_object(self.bucket, object_key)
            return FileInfo(
                storage_type="minio",
                object_key=object_key,
                file_size=stat.size,
                content_type=stat.content_type or "application/octet-stream",
                created_at=stat.last_modified
            )
        except Exception:
            return None

    async def health_check(self) -> Tuple[bool, str]:
        """健康检查"""
        try:
            client = self._get_client()
            if client.bucket_exists(self.bucket):
                return True, f"MinIO connected: {self.endpoint}/{self.bucket}"
            else:
                return False, f"MinIO bucket not found: {self.bucket}"
        except Exception as e:
            return False, f"MinIO connection failed: {str(e)}"

    def get_full_path(self, object_key: str) -> str:
        """获取文件的访问路径（MinIO 返回对象键）"""
        return f"minio://{self.bucket}/{object_key}"


class StorageService:
    """
    统一存储服务

    根据配置选择存储适配器，提供统一的文件管理接口
    """

    def __init__(self, config: StorageConfig):
        self.config = config
        self._adapter: Optional[StorageAdapter] = None

    @property
    def adapter(self) -> StorageAdapter:
        """获取存储适配器（延迟初始化）"""
        if self._adapter is None:
            if self.config.storage_type == "minio":
                self._adapter = MinIOStorageAdapter(
                    endpoint=self.config.minio_endpoint,
                    access_key=self.config.minio_access_key,
                    secret_key=self.config.minio_secret_key,
                    bucket=self.config.minio_bucket,
                    secure=self.config.minio_secure
                )
            else:
                self._adapter = LocalStorageAdapter(
                    base_path=self.config.local_base_path
                )
        return self._adapter

    async def save_model(self, experiment_id: str, data: bytes, format: str = "json") -> FileInfo:
        """
        保存模型文件

        Args:
            experiment_id: 实验 ID
            data: 模型数据
            format: 模型格式（json, ubj）

        Returns:
            文件信息
        """
        object_key = f"models/{experiment_id}/model.{format}"
        content_type = "application/json" if format == "json" else "application/octet-stream"
        return await self.adapter.save(object_key, data, content_type)

    async def save_model_from_path(self, experiment_id: str, file_path: str, format: str = "json") -> FileInfo:
        """
        从本地路径保存模型文件

        Args:
            experiment_id: 实验 ID
            file_path: 本地文件路径
            format: 模型格式

        Returns:
            文件信息
        """
        object_key = f"models/{experiment_id}/model.{format}"
        content_type = "application/json" if format == "json" else "application/octet-stream"
        return await self.adapter.save_from_file(object_key, file_path, content_type)

    async def get_model(self, experiment_id: str, format: str = "json") -> bytes:
        """读取模型文件"""
        object_key = f"models/{experiment_id}/model.{format}"
        return await self.adapter.read(object_key)

    async def get_model_path(self, experiment_id: str, format: str = "json") -> str:
        """获取模型文件的访问路径"""
        object_key = f"models/{experiment_id}/model.{format}"
        return self.adapter.get_full_path(object_key)

    async def save_preprocessing_output(
        self,
        dataset_id: str,
        task_id: str,
        data: bytes,
        filename: str = "processed.csv"
    ) -> FileInfo:
        """保存预处理输出"""
        object_key = f"preprocessing/{dataset_id}/{task_id}/{filename}"
        return await self.adapter.save(object_key, data, "text/csv")

    async def save_feature_engineering_output(
        self,
        dataset_id: str,
        task_id: str,
        data: bytes,
        filename: str = "features.csv"
    ) -> FileInfo:
        """保存特征工程输出"""
        object_key = f"feature_engineering/{dataset_id}/{task_id}/{filename}"
        return await self.adapter.save(object_key, data, "text/csv")

    async def health_check(self) -> Tuple[bool, str]:
        """健康检查"""
        return await self.adapter.health_check()

    @property
    def storage_type(self) -> str:
        """当前存储类型"""
        return self.config.storage_type


# 全局存储服务实例
_storage_service: Optional[StorageService] = None


def get_storage_service() -> StorageService:
    """
    获取存储服务单例

    必须先调用 init_storage_service 初始化
    """
    global _storage_service
    if _storage_service is None:
        raise RuntimeError("Storage service not initialized. Call init_storage_service first.")
    return _storage_service


async def init_storage_service(config: Optional[StorageConfig] = None) -> StorageService:
    """
    初始化存储服务

    Args:
        config: 存储配置，如果为 None 则从环境变量读取

    Returns:
        存储服务实例
    """
    global _storage_service

    if config is None:
        import os
        config = StorageConfig(
            storage_type=os.getenv("STORAGE_TYPE", "local"),
            local_base_path=os.getenv("WORKSPACE_DIR", "./workspace"),
            minio_endpoint=os.getenv("MINIO_ENDPOINT", "localhost:9000"),
            minio_access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
            minio_secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
            minio_bucket=os.getenv("MINIO_BUCKET", "xgboost-vis"),
            minio_secure=os.getenv("MINIO_SECURE", "false").lower() == "true"
        )

    _storage_service = StorageService(config)
    logger.info(f"Storage service initialized: type={config.storage_type}")
    return _storage_service