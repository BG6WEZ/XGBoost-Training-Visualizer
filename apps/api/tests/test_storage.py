"""
存储服务测试

测试统一存储适配层功能
"""
import pytest
import pytest_asyncio
import os
import tempfile
import asyncio

# 设置测试环境
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://localhost:6379/15"
os.environ["STORAGE_TYPE"] = "local"


class TestLocalStorageAdapter:
    """本地存储适配器测试"""

    @pytest.mark.asyncio
    async def test_local_storage_save_and_read(self):
        """测试本地存储保存和读取"""
        from app.services.storage import LocalStorageAdapter
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            adapter = LocalStorageAdapter(base_path=tmpdir)

            # 保存文件
            test_data = b"test model data content"
            result = await adapter.save("models/test-exp/model.json", test_data)

            assert result.storage_type == "local"
            assert result.object_key == "models/test-exp/model.json"
            assert result.file_size == len(test_data)

            # 读取文件
            read_data = await adapter.read("models/test-exp/model.json")
            assert read_data == test_data

    @pytest.mark.asyncio
    async def test_local_storage_exists(self):
        """测试文件存在检查"""
        from app.services.storage import LocalStorageAdapter
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            adapter = LocalStorageAdapter(base_path=tmpdir)

            # 文件不存在
            assert await adapter.exists("nonexistent.txt") is False

            # 保存后存在
            await adapter.save("test.txt", b"content")
            assert await adapter.exists("test.txt") is True

    @pytest.mark.asyncio
    async def test_local_storage_delete(self):
        """测试文件删除"""
        from app.services.storage import LocalStorageAdapter
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            adapter = LocalStorageAdapter(base_path=tmpdir)

            await adapter.save("to_delete.txt", b"content")
            assert await adapter.exists("to_delete.txt") is True

            result = await adapter.delete("to_delete.txt")
            assert result is True
            assert await adapter.exists("to_delete.txt") is False

    @pytest.mark.asyncio
    async def test_local_storage_get_info(self):
        """测试获取文件信息"""
        from app.services.storage import LocalStorageAdapter
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            adapter = LocalStorageAdapter(base_path=tmpdir)

            test_data = b"test content for info"
            await adapter.save("info_test.json", test_data)

            info = await adapter.get_info("info_test.json")
            assert info is not None
            assert info.storage_type == "local"
            assert info.file_size == len(test_data)
            assert info.content_type == "application/json"

    @pytest.mark.asyncio
    async def test_local_storage_health_check(self):
        """测试健康检查"""
        from app.services.storage import LocalStorageAdapter
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            adapter = LocalStorageAdapter(base_path=tmpdir)
            is_healthy, message = await adapter.health_check()
            assert is_healthy is True
            assert "ready" in message.lower()

    @pytest.mark.asyncio
    async def test_local_storage_get_full_path(self):
        """测试获取完整路径"""
        from app.services.storage import LocalStorageAdapter
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            adapter = LocalStorageAdapter(base_path=tmpdir)
            full_path = adapter.get_full_path("models/test/model.json")
            assert "models/test/model.json" in full_path


class TestStorageService:
    """存储服务测试"""

    @pytest.mark.asyncio
    async def test_storage_service_save_model(self):
        """测试保存模型"""
        from app.services.storage import StorageService, StorageConfig
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            config = StorageConfig(
                storage_type="local",
                local_base_path=tmpdir
            )
            service = StorageService(config)

            model_data = b'{"model": "xgboost", "version": "1.0"}'
            result = await service.save_model("exp-001", model_data, "json")

            assert result.storage_type == "local"
            assert "models/exp-001/model.json" in result.object_key

    @pytest.mark.asyncio
    async def test_storage_service_save_from_file(self):
        """测试从文件保存"""
        from app.services.storage import StorageService, StorageConfig
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            config = StorageConfig(
                storage_type="local",
                local_base_path=tmpdir
            )
            service = StorageService(config)

            # 创建临时文件
            src_file = os.path.join(tmpdir, "source_model.json")
            with open(src_file, "w") as f:
                f.write('{"model": "test"}')

            result = await service.save_model_from_path("exp-002", src_file, "json")
            assert result.storage_type == "local"
            assert result.file_size > 0

    @pytest.mark.asyncio
    async def test_storage_service_get_model(self):
        """测试读取模型"""
        from app.services.storage import StorageService, StorageConfig
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            config = StorageConfig(
                storage_type="local",
                local_base_path=tmpdir
            )
            service = StorageService(config)

            model_data = b"model binary data"
            await service.save_model("exp-003", model_data, "json")

            read_data = await service.get_model("exp-003", "json")
            assert read_data == model_data

    @pytest.mark.asyncio
    async def test_storage_service_preprocessing_output(self):
        """测试预处理输出保存"""
        from app.services.storage import StorageService, StorageConfig
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            config = StorageConfig(
                storage_type="local",
                local_base_path=tmpdir
            )
            service = StorageService(config)

            csv_data = b"col1,col2\n1,2\n3,4"
            result = await service.save_preprocessing_output("dataset-001", "task-001", csv_data)

            assert result.storage_type == "local"
            assert "preprocessing" in result.object_key

    @pytest.mark.asyncio
    async def test_storage_service_feature_engineering_output(self):
        """测试特征工程输出保存"""
        from app.services.storage import StorageService, StorageConfig
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            config = StorageConfig(
                storage_type="local",
                local_base_path=tmpdir
            )
            service = StorageService(config)

            csv_data = b"col1,col2,col3\n1,2,3"
            result = await service.save_feature_engineering_output("dataset-001", "task-002", csv_data)

            assert result.storage_type == "local"
            assert "feature_engineering" in result.object_key


class TestWorkerAPIStorageIntegration:
    """
    Worker-API 存储集成测试

    模拟 Worker 保存模型后，API 通过同一 storage 配置下载成功
    """

    @pytest.mark.asyncio
    async def test_worker_save_api_read_integration(self):
        """
        R8: 真实集成测试 - Worker 保存模型后 API 下载成功

        模拟：
        1. Worker 使用 StorageService 保存模型
        2. API 使用同一 StorageService 配置读取模型
        """
        from app.services.storage import StorageService, StorageConfig, init_storage_service, get_storage_service
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            # 1. 模拟 Worker 初始化存储服务
            worker_config = StorageConfig(
                storage_type="local",
                local_base_path=tmpdir  # 统一使用 WORKSPACE_DIR
            )
            worker_storage = StorageService(worker_config)

            # 2. Worker 保存模型
            experiment_id = "exp-integration-test-001"
            model_content = b'{"model_type": "xgboost", "version": "1.0", "trees": [{"tree": 1}]}'

            save_result = await worker_storage.save_model(
                experiment_id=experiment_id,
                data=model_content,
                format="json"
            )

            # 验证保存成功
            assert save_result.storage_type == "local"
            assert save_result.file_size == len(model_content)
            assert experiment_id in save_result.object_key

            # 3. 模拟 API 使用同一存储配置初始化
            # 重置全局存储服务
            import app.services.storage as storage_module
            storage_module._storage_service = None

            api_config = StorageConfig(
                storage_type="local",
                local_base_path=tmpdir  # 与 Worker 使用相同的 WORKSPACE_DIR
            )
            await init_storage_service(api_config)

            # 4. API 读取模型
            api_storage = get_storage_service()
            read_content = await api_storage.get_model(experiment_id, "json")

            # 5. 验证内容一致
            assert read_content == model_content, "API 读取的模型内容与 Worker 保存的不一致"

    @pytest.mark.asyncio
    async def test_different_task_id_different_object_key(self):
        """
        R9: 不同 task_id 的预处理/特征工程输出对象键必须不同
        """
        from app.services.storage import StorageService, StorageConfig
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            config = StorageConfig(
                storage_type="local",
                local_base_path=tmpdir
            )
            service = StorageService(config)

            dataset_id = "dataset-001"

            # 同一 dataset 不同 task_id 的预处理输出
            result1 = await service.save_preprocessing_output(
                dataset_id=dataset_id,
                task_id="task-001",
                data=b"col1,col2\n1,2"
            )

            result2 = await service.save_preprocessing_output(
                dataset_id=dataset_id,
                task_id="task-002",
                data=b"col1,col2\n3,4"
            )

            # 验证对象键不同
            assert result1.object_key != result2.object_key, \
                f"不同 task_id 的预处理输出对象键应该不同: {result1.object_key} vs {result2.object_key}"

            # 验证对象键包含正确的 task_id
            assert "task-001" in result1.object_key, f"对象键应包含 task_id: {result1.object_key}"
            assert "task-002" in result2.object_key, f"对象键应包含 task_id: {result2.object_key}"

            # 特征工程输出同样验证
            result3 = await service.save_feature_engineering_output(
                dataset_id=dataset_id,
                task_id="task-003",
                data=b"col1,col2,col3\n1,2,3"
            )

            result4 = await service.save_feature_engineering_output(
                dataset_id=dataset_id,
                task_id="task-004",
                data=b"col1,col2,col3\n4,5,6"
            )

            assert result3.object_key != result4.object_key, \
                f"不同 task_id 的特征工程输出对象键应该不同: {result3.object_key} vs {result4.object_key}"

            assert "task-003" in result3.object_key, f"对象键应包含 task_id: {result3.object_key}"
            assert "task-004" in result4.object_key, f"对象键应包含 task_id: {result4.object_key}"

    @pytest.mark.asyncio
    async def test_preprocessing_and_feature_engineering_different_paths(self):
        """
        预处理和特征工程输出路径应该不同
        """
        from app.services.storage import StorageService, StorageConfig
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            config = StorageConfig(
                storage_type="local",
                local_base_path=tmpdir
            )
            service = StorageService(config)

            dataset_id = "dataset-001"
            task_id = "task-001"

            preprocessing_result = await service.save_preprocessing_output(
                dataset_id=dataset_id,
                task_id=task_id,
                data=b"col1,col2\n1,2"
            )

            feature_result = await service.save_feature_engineering_output(
                dataset_id=dataset_id,
                task_id=task_id,
                data=b"col1,col2,col3\n1,2,3"
            )

            # 验证路径不同
            assert preprocessing_result.object_key != feature_result.object_key

            # 验证路径前缀正确
            assert preprocessing_result.object_key.startswith("preprocessing/")
            assert feature_result.object_key.startswith("feature_engineering/")