#!/usr/bin/env python
"""
回归验证脚本

提供可复用的回归测试入口，包含：
1. 路径一致性测试（API 和 Worker 的 WORKSPACE_DIR）
2. 核心链路冒烟验证

使用方法：
    # 运行完整回归验证
    python scripts/regression_check.py

    # 仅运行路径一致性测试
    python scripts/regression_check.py --path-only

    # 仅运行冒烟测试
    python scripts/regression_check.py --smoke-only

    # 详细输出
    python scripts/regression_check.py -v
"""
import argparse
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
    """
    执行命令并返回结果

    Args:
        cmd: 命令及参数列表
        cwd: 工作目录

    Returns:
        (return_code, stdout, stderr)
    """
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.returncode, result.stdout, result.stderr


def check_workspace_consistency(verbose: bool = False) -> bool:
    """
    检查 workspace 路径一致性

    验证 API 和 Worker 的 WORKSPACE_DIR 配置一致

    Returns:
        True 表示通过，False 表示失败
    """
    print("\n" + "=" * 60)
    print("1. Workspace 路径一致性检查")
    print("=" * 60)

    api_dir = Path(__file__).parent.parent
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_workspace_consistency.py",
        "-v" if verbose else "-q",
        "--tb=short",
    ]

    returncode, stdout, stderr = run_command(cmd, cwd=api_dir)

    if verbose:
        print(stdout)
        if stderr:
            print(stderr)

    if returncode == 0:
        print("[PASS] Workspace 路径一致性检查通过")
        return True
    else:
        print("[FAIL] Workspace 路径一致性检查失败")
        print(stdout)
        if stderr:
            print(stderr)
        return False


def run_smoke_tests(verbose: bool = False) -> bool:
    """
    运行冒烟测试

    验证核心链路功能正常

    Returns:
        True 表示通过，False 表示失败
    """
    print("\n" + "=" * 60)
    print("2. 核心链路冒烟测试")
    print("=" * 60)

    api_dir = Path(__file__).parent.parent

    # 选择关键测试用例作为冒烟测试
    smoke_tests = [
        # 存储服务核心功能
        "tests/test_storage.py::TestLocalStorageAdapter::test_local_storage_save_and_read",
        # 数据集核心功能
        "tests/test_datasets.py::TestDatasetAPI::test_create_dataset_with_single_file",
        # 实验核心功能
        "tests/test_experiments.py::TestExperimentAPI::test_create_experiment",
        # 结果核心功能
        "tests/test_results.py::TestResultsEndpoints::test_get_results_happy_path",
    ]

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        *smoke_tests,
        "-v" if verbose else "-q",
        "--tb=short",
    ]

    returncode, stdout, stderr = run_command(cmd, cwd=api_dir)

    if verbose:
        print(stdout)
        if stderr:
            print(stderr)

    if returncode == 0:
        print("[PASS] 核心链路冒烟测试通过")
        return True
    else:
        print("[FAIL] 核心链路冒烟测试失败")
        print(stdout)
        if stderr:
            print(stderr)
        return False


def run_full_regression(verbose: bool = False) -> bool:
    """
    运行完整回归测试

    Returns:
        True 表示全部通过，False 表示有失败
    """
    print("\n" + "=" * 60)
    print("XGBoost Training Visualizer - 回归验证")
    print("=" * 60)

    results = []

    # 1. 路径一致性检查
    results.append(check_workspace_consistency(verbose))

    # 2. 冒烟测试
    results.append(run_smoke_tests(verbose))

    # 汇总结果
    print("\n" + "=" * 60)
    print("回归验证结果汇总")
    print("=" * 60)

    all_passed = all(results)

    if all_passed:
        print("[SUCCESS] 所有回归验证通过")
        return True
    else:
        print("[FAILED] 部分回归验证失败")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="XGBoost Training Visualizer 回归验证脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    # 运行完整回归验证
    python scripts/regression_check.py

    # 仅运行路径一致性测试
    python scripts/regression_check.py --path-only

    # 仅运行冒烟测试
    python scripts/regression_check.py --smoke-only

    # 详细输出
    python scripts/regression_check.py -v
        """,
    )
    parser.add_argument(
        "--path-only",
        action="store_true",
        help="仅运行路径一致性测试",
    )
    parser.add_argument(
        "--smoke-only",
        action="store_true",
        help="仅运行冒烟测试",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="详细输出",
    )

    args = parser.parse_args()

    if args.path_only:
        success = check_workspace_consistency(args.verbose)
    elif args.smoke_only:
        success = run_smoke_tests(args.verbose)
    else:
        success = run_full_regression(args.verbose)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
