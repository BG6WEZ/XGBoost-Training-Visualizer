"""
Worker 端存储服务

与 API 端共享相同的存储适配层逻辑
"""
import os
import logging
import aiofiles
from abc import ABC, abstractmethod
from typing import Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class StorageAdapter(ABC):
    """存储适配器基类"""

    @abstractmethod
    async def save(self, object_key: str, data: bytes, content_type: str = "application/octet-stream"):
        """保存文件"""
        pass

    @abstractmethod
    async def save_from_file(self, object_key: str, file_path: str, content_type: str = "application/octet-stream"):
        """从本地文件保存"""
        pass

    @abstractmethod
    async def health_check(self) -> Tuple[bool, str]:
        """健康检查"""
        pass

    @abstractmethod
    def get_full_path(self, object_key: str) -> str:
        """获取文件的完整访问路径"""
        pass

    @abstractmethod
    def storage_type(self) -> str:
        """存储类型"""
        pass


class LocalStorageAdapter(StorageAdapter):
    """本地文件系统存储适配器"""

    def __init__(self, base_path: str = "./workspace"):
        self._base_path = os.path.abspath(base_path)
        os.makedirs(self._base_path, exist_ok=True)
        logger.info(f"LocalStorageAdapter initialized with base_path: {self._base_path}")

    @property
    def storage_type(self) -> str:
        return "local"

    def _get_full_path(self, object_key: str) -> str:
        return os.path.join(self._base_path, object_key)

    async def save(self, object_key: str, data: bytes, content_type: str = "application/octet-stream"):
        """保存文件"""
        full_path = self._get_full_path(object_key)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        async with aiofiles.open(full_path, 'wb') as f:
            await f.write(data)

        file_size = len(data)
        logger.info(f"File saved: {object_key} ({file_size} bytes)")

        return {
            "storage_type": "local",
            "object_key": object_key,
            "full_path": full_path,
            "file_size": file_size
        }

    async def save_from_file(self, object_key: str, file_path: str, content_type: str = "application/octet-stream"):
        """从本地文件保存（复制到目标位置）"""
        full_path = self._get_full_path(object_key)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        import shutil
        shutil.copy2(file_path, full_path)

        file_size = os.path.getsize(full_path)
        logger.info(f"File copied to: {object_key} ({file_size} bytes)")

        return {
            "storage_type": "local",
            "object_key": object_key,
            "full_path": full_path,
            "file_size": file_size
        }

    async def health_check(self) -> Tuple[bool, str]:
        try:
            if os.path.exists(self._base_path) and os.access(self._base_path, os.W_OK):
                return True, f"Local storage ready at {self._base_path}"
            return False, f"Local storage not accessible: {self._base_path}"
        except Exception as e:
            return False, f"Local storage error: {str(e)}"

    def get_full_path(self, object_key: str) -> str:
        return self._get_full_path(object_key)


class MinIOStorageAdapter(StorageAdapter):
    """MinIO 对象存储适配器"""

    def __init__(self, endpoint: str, access_key: str, secret_key: str, bucket: str, secure: bool = False):
        self._endpoint = endpoint
        self._access_key = access_key
        self._secret_key = secret_key
        self._bucket = bucket
        self._secure = secure
        self._client = None
        logger.info(f"MinIOStorageAdapter configured for {endpoint}/{bucket}")

    @property
    def storage_type(self) -> str:
        return "minio"

    def _get_client(self):
        if self._client is None:
            from minio import Minio
            self._client = Minio(
                self._endpoint,
                access_key=self._access_key,
                secret_key=self._secret_key,
                secure=self._secure
            )
            if not self._client.bucket_exists(self._bucket):
                self._client.make_bucket(self._bucket)
        return self._client

    async def save(self, object_key: str, data: bytes, content_type: str = "application/octet-stream"):
        import io
        client = self._get_client()
        data_stream = io.BytesIO(data)

        client.put_object(self._bucket, object_key, data_stream, len(data), content_type)

        logger.info(f"File saved to MinIO: {object_key} ({len(data)} bytes)")

        return {
            "storage_type": "minio",
            "object_key": object_key,
            "file_size": len(data)
        }

    async def save_from_file(self, object_key: str, file_path: str, content_type: str = "application/octet-stream"):
        client = self._get_client()
        file_size = os.path.getsize(file_path)

        client.fput_object(self._bucket, object_key, file_path, content_type)

        logger.info(f"File uploaded to MinIO: {object_key} ({file_size} bytes)")

        return {
            "storage_type": "minio",
            "object_key": object_key,
            "file_size": file_size
        }

    async def health_check(self) -> Tuple[bool, str]:
        try:
            client = self._get_client()
            if client.bucket_exists(self._bucket):
                return True, f"MinIO connected: {self._endpoint}/{self._bucket}"
            return False, f"MinIO bucket not found: {self._bucket}"
        except Exception as e:
            return False, f"MinIO connection failed: {str(e)}"

    def get_full_path(self, object_key: str) -> str:
        return f"minio://{self._bucket}/{object_key}"


class StorageService:
    """统一存储服务"""

    def __init__(self, storage_type: str = "local", **kwargs):
        self._adapter: Optional[StorageAdapter] = None
        self._storage_type = storage_type
        self._config = kwargs

    @property
    def adapter(self) -> StorageAdapter:
        if self._adapter is None:
            if self._storage_type == "minio":
                self._adapter = MinIOStorageAdapter(
                    endpoint=self._config.get("minio_endpoint", "localhost:9000"),
                    access_key=self._config.get("minio_access_key", "minioadmin"),
                    secret_key=self._config.get("minio_secret_key", "minioadmin"),
                    bucket=self._config.get("minio_bucket", "xgboost-vis"),
                    secure=self._config.get("minio_secure", False)
                )
            else:
                self._adapter = LocalStorageAdapter(
                    base_path=self._config.get("local_base_path", "./workspace")
                )
        return self._adapter

    async def save_model(self, experiment_id: str, data: bytes, format: str = "json"):
        """保存模型文件"""
        object_key = f"models/{experiment_id}/model.{format}"
        content_type = "application/json" if format == "json" else "application/octet-stream"
        result = await self.adapter.save(object_key, data, content_type)
        return result

    async def save_model_from_path(self, experiment_id: str, file_path: str, format: str = "json"):
        """从本地路径保存模型"""
        object_key = f"models/{experiment_id}/model.{format}"
        content_type = "application/json" if format == "json" else "application/octet-stream"
        result = await self.adapter.save_from_file(object_key, file_path, content_type)
        return result

    async def save_preprocessing_output(self, dataset_id: str, task_id: str, data: bytes, filename: str = "processed.csv"):
        """保存预处理输出"""
        object_key = f"preprocessing/{dataset_id}/{task_id}/{filename}"
        return await self.adapter.save(object_key, data, "text/csv")

    async def save_feature_engineering_output(self, dataset_id: str, task_id: str, data: bytes, filename: str = "features.csv"):
        """保存特征工程输出"""
        object_key = f"feature_engineering/{dataset_id}/{task_id}/{filename}"
        return await self.adapter.save(object_key, data, "text/csv")

    async def health_check(self) -> Tuple[bool, str]:
        return await self.adapter.health_check()

    def get_model_object_key(self, experiment_id: str, format: str = "json") -> str:
        """获取模型对象键"""
        return f"models/{experiment_id}/model.{format}"

    @property
    def storage_type(self) -> str:
        return self._storage_type


# 全局实例
_storage_service: Optional[StorageService] = None


def get_storage_service() -> StorageService:
    global _storage_service
    if _storage_service is None:
        raise RuntimeError("Storage service not initialized")
    return _storage_service


def init_storage_service(
    storage_type: str = "local",
    local_base_path: str = "./workspace",
    minio_endpoint: str = "localhost:9000",
    minio_access_key: str = "minioadmin",
    minio_secret_key: str = "minioadmin",
    minio_bucket: str = "xgboost-vis",
    minio_secure: bool = False
) -> StorageService:
    """初始化存储服务"""
    global _storage_service

    _storage_service = StorageService(
        storage_type=storage_type,
        local_base_path=local_base_path,
        minio_endpoint=minio_endpoint,
        minio_access_key=minio_access_key,
        minio_secret_key=minio_secret_key,
        minio_bucket=minio_bucket,
        minio_secure=minio_secure
    )

    logger.info(f"Storage service initialized: type={storage_type}")
    return _storage_service