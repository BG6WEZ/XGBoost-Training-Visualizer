"""
Workspace 一致性守卫测试

验证 API 和 Worker 的 WORKSPACE_DIR 解析一致性
确保两个服务使用相同的 workspace 目录
"""
import pytest
import os
import sys
import importlib.util
from pathlib import Path


def load_worker_settings():
    """
    动态加载 Worker 的配置
    
    Returns:
        Worker 的 settings 对象
    """
    worker_config_path = Path(__file__).parent.parent.parent / "worker" / "app" / "config.py"
    
    if not worker_config_path.exists():
        pytest.skip(f"Worker 配置文件不存在: {worker_config_path}")
    
    # 使用 importlib 动态加载模块
    spec = importlib.util.spec_from_file_location("worker_config", worker_config_path)
    worker_config_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(worker_config_module)
    
    return worker_config_module.settings


class TestWorkspaceConsistency:
    """Workspace 一致性测试类"""

    def test_workspace_dir_config_consistency(self):
        """
        测试 API 和 Worker 的 WORKSPACE_DIR 配置值一致
        
        Given: API 和 Worker 各自的配置文件
        When: 读取两个服务的 WORKSPACE_DIR 配置
        Then: 配置值应该完全相同
        """
        # 导入 API 配置
        from app.config import settings as api_settings
        
        # 加载 Worker 配置
        worker_settings = load_worker_settings()
        
        # 验证配置值一致
        assert api_settings.WORKSPACE_DIR == worker_settings.WORKSPACE_DIR, \
            f"API 和 Worker 的 WORKSPACE_DIR 配置不一致: API={api_settings.WORKSPACE_DIR}, Worker={worker_settings.WORKSPACE_DIR}"

    def test_workspace_dir_is_absolute_path(self):
        """
        测试 WORKSPACE_DIR 是绝对路径
        
        Given: API 和 Worker 的 WORKSPACE_DIR 配置
        When: 检查路径类型
        Then: 路径必须是绝对路径
        """
        # 导入 API 配置
        from app.config import settings as api_settings
        
        # 加载 Worker 配置
        worker_settings = load_worker_settings()
        
        # 验证 API 的 WORKSPACE_DIR 是绝对路径
        api_workspace = Path(api_settings.WORKSPACE_DIR)
        assert api_workspace.is_absolute(), \
            f"API 的 WORKSPACE_DIR 应该是绝对路径: {api_settings.WORKSPACE_DIR}"
        
        # 验证 Worker 的 WORKSPACE_DIR 是绝对路径
        worker_workspace = Path(worker_settings.WORKSPACE_DIR)
        assert worker_workspace.is_absolute(), \
            f"Worker 的 WORKSPACE_DIR 应该是绝对路径: {worker_settings.WORKSPACE_DIR}"

    def test_workspace_dir_points_to_project_root_workspace(self):
        """
        测试 WORKSPACE_DIR 指向项目根目录下的 workspace
        
        Given: API 和 Worker 的 WORKSPACE_DIR 配置
        When: 检查路径结构
        Then: 路径应该指向项目根目录下的 workspace 目录
        """
        # 导入 API 配置
        from app.config import settings as api_settings
        
        # 加载 Worker 配置
        worker_settings = load_worker_settings()
        
        # 验证路径以 workspace 结尾
        api_workspace = Path(api_settings.WORKSPACE_DIR)
        assert api_workspace.name == "workspace", \
            f"API 的 WORKSPACE_DIR 应该指向 workspace 目录: {api_settings.WORKSPACE_DIR}"
        
        worker_workspace = Path(worker_settings.WORKSPACE_DIR)
        assert worker_workspace.name == "workspace", \
            f"Worker 的 WORKSPACE_DIR 应该指向 workspace 目录: {worker_settings.WORKSPACE_DIR}"

    def test_workspace_dir_not_empty(self):
        """
        测试 WORKSPACE_DIR 不为空
        
        Given: API 和 Worker 的配置
        When: 检查 WORKSPACE_DIR 值
        Then: 配置值不应为空字符串
        """
        # 导入 API 配置
        from app.config import settings as api_settings
        
        # 加载 Worker 配置
        worker_settings = load_worker_settings()
        
        # 验证 API 的 WORKSPACE_DIR 不为空
        assert api_settings.WORKSPACE_DIR, "API 的 WORKSPACE_DIR 不应为空"
        assert api_settings.WORKSPACE_DIR.strip(), "API 的 WORKSPACE_DIR 不应为空白字符串"
        
        # 验证 Worker 的 WORKSPACE_DIR 不为空
        assert worker_settings.WORKSPACE_DIR, "Worker 的 WORKSPACE_DIR 不应为空"
        assert worker_settings.WORKSPACE_DIR.strip(), "Worker 的 WORKSPACE_DIR 不应为空白字符串"

    def test_workspace_dir_path_format_valid(self):
        """
        测试 WORKSPACE_DIR 路径格式有效
        
        Given: API 和 Worker 的 WORKSPACE_DIR 配置
        When: 验证路径格式
        Then: 路径不应包含非法字符或格式错误
        """
        # 导入 API 配置
        from app.config import settings as api_settings
        
        # 加载 Worker 配置
        worker_settings = load_worker_settings()
        
        # 验证 API 的路径格式
        api_workspace = Path(api_settings.WORKSPACE_DIR)
        # Path 对象创建成功即表示路径格式有效
        
        # 验证 Worker 的路径格式
        worker_workspace = Path(worker_settings.WORKSPACE_DIR)
        # Path 对象创建成功即表示路径格式有效
        
        # 验证路径不包含上级目录遍历（安全检查）
        assert ".." not in str(api_workspace), \
            f"API 的 WORKSPACE_DIR 不应包含 '..': {api_settings.WORKSPACE_DIR}"
        assert ".." not in str(worker_workspace), \
            f"Worker 的 WORKSPACE_DIR 不应包含 '..': {worker_settings.WORKSPACE_DIR}"

    @pytest.mark.integration
    def test_workspace_dir_exists_or_creatable(self):
        """
        集成测试：验证 workspace 目录存在或可创建
        
        Given: API 和 Worker 的 WORKSPACE_DIR 配置
        When: 检查目录是否存在
        Then: 目录应该存在，或者可以成功创建
        """
        # 导入 API 配置
        from app.config import settings as api_settings
        
        # 获取绝对路径
        workspace_path = Path(api_settings.WORKSPACE_DIR)
        
        # 检查目录是否存在
        if workspace_path.exists():
            assert workspace_path.is_dir(), \
                f"WORKSPACE_DIR 路径存在但不是目录: {workspace_path}"
            print(f"\nWorkspace 目录已存在: {workspace_path}")
        else:
            # 尝试创建目录（测试权限）
            try:
                workspace_path.mkdir(parents=True, exist_ok=True)
                print(f"\n成功创建 Workspace 目录: {workspace_path}")
                # 清理：删除刚创建的空目录
                if workspace_path.exists() and not any(workspace_path.iterdir()):
                    workspace_path.rmdir()
            except PermissionError:
                pytest.skip(f"无权限创建 workspace 目录: {workspace_path}")
            except Exception as e:
                pytest.fail(f"无法创建 workspace 目录: {e}")


class TestWorkspaceAbsolutePathValidation:
    """Workspace 绝对路径验证测试类"""

    def test_api_workspace_is_absolute(self):
        """
        测试 API 的 WORKSPACE_DIR 是绝对路径
        
        Given: API 的 WORKSPACE_DIR 配置
        When: 检查路径类型
        Then: 路径必须是绝对路径
        """
        from app.config import settings as api_settings
        
        workspace_dir = api_settings.WORKSPACE_DIR
        workspace_path = Path(workspace_dir)
        
        assert workspace_path.is_absolute(), \
            f"API 的 WORKSPACE_DIR 应该是绝对路径: {workspace_dir}"

    def test_worker_workspace_is_absolute(self):
        """
        测试 Worker 的 WORKSPACE_DIR 是绝对路径
        
        Given: Worker 的 WORKSPACE_DIR 配置
        When: 检查路径类型
        Then: 路径必须是绝对路径
        """
        worker_settings = load_worker_settings()
        
        workspace_dir = worker_settings.WORKSPACE_DIR
        workspace_path = Path(workspace_dir)
        
        assert workspace_path.is_absolute(), \
            f"Worker 的 WORKSPACE_DIR 应该是绝对路径: {workspace_dir}"

    def test_both_services_have_identical_workspace_path(self):
        """
        测试两个服务使用完全相同的 workspace 路径
        
        Given: API 和 Worker 的 WORKSPACE_DIR 配置
        When: 比较路径值
        Then: 两个路径必须完全相同（字符串比较）
        """
        from app.config import settings as api_settings
        
        worker_settings = load_worker_settings()
        
        # 验证两个路径完全相同
        assert api_settings.WORKSPACE_DIR == worker_settings.WORKSPACE_DIR, \
            f"API 和 Worker 的 workspace 路径不同: API={api_settings.WORKSPACE_DIR}, Worker={worker_settings.WORKSPACE_DIR}"
        
        # 验证路径是绝对路径
        api_path = Path(api_settings.WORKSPACE_DIR)
        worker_path = Path(worker_settings.WORKSPACE_DIR)
        
        assert api_path.is_absolute(), \
            f"API 的路径不是绝对路径: {api_settings.WORKSPACE_DIR}"
        assert worker_path.is_absolute(), \
            f"Worker 的路径不是绝对路径: {worker_settings.WORKSPACE_DIR}"
