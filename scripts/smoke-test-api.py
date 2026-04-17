#!/usr/bin/env python
"""
API 集成冒烟测试脚本

覆盖从登录、数据集、实验、训练、结果到登出的核心 API 链路。
使用 Python + httpx 实现。

用法:
    python scripts/smoke-test-api.py --api-url http://localhost:8000
"""

import asyncio
import argparse
import time
import sys
import os
import uuid
from typing import Optional, Any, Dict


try:
    import httpx
except ImportError:
    print("ERROR: httpx is not installed. Please run: pip install httpx")
    sys.exit(1)


# ========== 配置 ==========

# 默认管理员账号（与 create_admin.py 脚本一致）
_DEFAULT_USERNAME = "admin"
_DEFAULT_PASSWORD = "admin123"

# 超时设置
REQUEST_TIMEOUT = 30  # 秒
TRAINING_POLL_TIMEOUT = 300  # 训练轮询最大超时（秒）
TRAINING_POLL_INTERVAL = 10  # 轮询间隔（秒）


# ========== 测试结果记录 ==========

class TestResult:
    """单个测试步骤的结果"""
    def __init__(self, name: str):
        self.name = name
        self.status: Optional[str] = None  # "PASS" or "FAIL"
        self.duration: float = 0.0
        self.error: Optional[str] = None
        self.data: Optional[Dict[str, Any]] = None


class TestReport:
    """测试报告"""
    def __init__(self):
        self.results: list["TestResult"] = []

    def add_result(self, result: "TestResult"):
        self.results.append(result)

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.status == "PASS")

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if r.status == "FAIL")

    @property
    def all_passed(self) -> bool:
        return self.failed == 0 and len(self.results) > 0

    def print_summary(self):
        total = len(self.results)
        print("\n" + "=" * 60)
        print("冒烟测试报告")
        print("=" * 60)
        print(f"总步骤数: {total}")
        print(f"通过: {self.passed}")
        print(f"失败: {self.failed}")
        print("=" * 60)

        for r in self.results:
            status_str = f"[{r.status}]" if r.status else "[???]"
            duration_str = f"{r.duration:.2f}s"
            if r.status == "PASS":
                print(f"  {status_str} {r.name} ({duration_str})")
            else:
                print(f"  {status_str} {r.name} ({duration_str}) - ERROR: {r.error}")

        print("=" * 60)
        if self.all_passed:
            print("结果: 全部通过")
        else:
            print("结果: 存在失败")
        print("=" * 60)


# ========== 辅助函数 ==========

def make_step(name: str) -> TestResult:
    """创建一个测试步骤"""
    return TestResult(name)


async def run_step(step: TestResult, coro) -> TestResult:
    """执行一个测试步骤并记录结果"""
    start = time.time()
    try:
        result = await coro
        step.status = "PASS"
        step.data = result
    except Exception as e:
        step.status = "FAIL"
        step.error = str(e)[:500]
    finally:
        step.duration = time.time() - start
    return step


def log_response(step: TestResult):
    """打印步骤结果"""
    status_str = f"[{step.status}]"
    duration_str = f"{step.duration:.2f}s"
    if step.status == "PASS":
        print(f"  {status_str} {step.name} ({duration_str})")
    else:
        print(f"  {status_str} {step.name} ({duration_str}) - ERROR: {step.error}")


# ========== 冒烟测试主逻辑 ==========

async def run_smoke_test(api_url: str, report: TestReport, username: str, password: str):
    """执行完整的冒烟测试链路"""

    base_url = api_url.rstrip("/")

    # --- Step 1: 登录 ---
    step = make_step("1. POST /api/auth/login (获取 token)")
    token = None
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        async def do_login():
            nonlocal token
            resp = await client.post(
                f"{base_url}/api/auth/login",
                json={"username": username, "password": password}
            )
            if resp.status_code != 200:
                raise Exception(f"Login failed: {resp.status_code} {resp.text}")
            data = resp.json()
            token = data.get("access_token")
            if not token:
                raise Exception("No access_token in login response")
            return data

        await run_step(step, do_login())
        report.add_result(step)
        log_response(step)

    if not token:
        print("\n[FATAL] 登录失败，无法继续后续测试")
        return

    headers = {"Authorization": f"Bearer {token}"}

    # --- Step 2: 扫描资产 ---
    step = make_step("2. GET /api/assets/scan (扫描资产)")
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        async def do_scan():
            resp = await client.get(f"{base_url}/api/assets/scan", headers=headers)
            if resp.status_code != 200:
                raise Exception(f"Scan failed: {resp.status_code} {resp.text}")
            return resp.json()

        await run_step(step, do_scan())
        report.add_result(step)
        log_response(step)

    # --- Step 3: 上传测试 CSV ---
    step = make_step("3. POST /api/datasets/upload (上传测试 CSV)")
    uploaded_file_path = None
    upload_file_name = None

    # 创建临时测试 CSV 文件
    test_csv_content = (
        "date,feature_a,feature_b,feature_c,target\n"
        "2024-01-01,1.0,2.0,3.0,10.0\n"
        "2024-01-02,1.1,2.1,3.1,10.5\n"
        "2024-01-03,1.2,2.2,3.2,11.0\n"
        "2024-01-04,1.3,2.3,3.3,11.5\n"
        "2024-01-05,1.4,2.4,3.4,12.0\n"
        "2024-01-06,1.5,2.5,3.5,12.5\n"
        "2024-01-07,1.6,2.6,3.6,13.0\n"
        "2024-01-08,1.7,2.7,3.7,13.5\n"
        "2024-01-09,1.8,2.8,3.8,14.0\n"
        "2024-01-10,1.9,2.9,3.9,14.5\n"
        "2024-01-11,2.0,3.0,4.0,15.0\n"
        "2024-01-12,2.1,3.1,4.1,15.5\n"
        "2024-01-13,2.2,3.2,4.2,16.0\n"
        "2024-01-14,2.3,3.3,4.3,16.5\n"
        "2024-01-15,2.4,3.4,4.4,17.0\n"
        "2024-01-16,2.5,3.5,4.5,17.5\n"
        "2024-01-17,2.6,3.6,4.6,18.0\n"
        "2024-01-18,2.7,3.7,4.7,18.5\n"
        "2024-01-19,2.8,3.8,4.8,19.0\n"
        "2024-01-20,2.9,3.9,4.9,19.5\n"
    )

    # 使用脚本所在目录的临时文件，避免权限问题
    script_dir = os.path.dirname(os.path.abspath(__file__))
    temp_csv_path = os.path.join(script_dir, f"smoke_test_data_{uuid.uuid4().hex[:8]}.csv")
    try:
        with open(temp_csv_path, 'w') as f:
            f.write(test_csv_content)

        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            async def do_upload():
                nonlocal uploaded_file_path, upload_file_name
                with open(temp_csv_path, 'rb') as f:
                    files = {"file": ("smoke_test.csv", f, "text/csv")}
                    resp = await client.post(
                        f"{base_url}/api/datasets/upload",
                        files=files,
                        headers=headers
                    )
                if resp.status_code != 200:
                    raise Exception(f"Upload failed: {resp.status_code} {resp.text}")
                data = resp.json()
                uploaded_file_path = data.get("file_path")
                upload_file_name = data.get("file_name")
                if not uploaded_file_path:
                    raise Exception("No file_path in upload response")
                return data

            await run_step(step, do_upload())
            report.add_result(step)
            log_response(step)
    finally:
        # 清理临时文件
        if os.path.exists(temp_csv_path):
            os.remove(temp_csv_path)

    # --- Step 4: 创建数据集 ---
    step = make_step("4. POST /api/datasets/ (创建数据集)")
    dataset_id: Optional[str] = None
    if uploaded_file_path:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            async def do_create_dataset():
                nonlocal dataset_id
                payload: Dict[str, Any] = {
                    "name": f"smoke_test_dataset_{uuid.uuid4().hex[:8]}",
                    "description": "Smoke test dataset",
                    "time_column": "date",
                    "target_column": "target",
                    "files": [
                        {
                            "file_path": uploaded_file_path,
                            "file_name": upload_file_name or "smoke_test.csv",
                            "role": "primary",
                            "row_count": 20,
                            "column_count": 5,
                            "file_size": len(test_csv_content.encode()),
                            "columns_info": [
                                {"name": "date", "dtype": "object", "is_numeric": False, "is_datetime": True},
                                {"name": "feature_a", "dtype": "float64", "is_numeric": True, "is_datetime": False},
                                {"name": "feature_b", "dtype": "float64", "is_numeric": True, "is_datetime": False},
                                {"name": "feature_c", "dtype": "float64", "is_numeric": True, "is_datetime": False},
                                {"name": "target", "dtype": "float64", "is_numeric": True, "is_datetime": False},
                            ]
                        }
                    ]
                }
                resp = await client.post(
                    f"{base_url}/api/datasets/",
                    json=payload,
                    headers={**headers, "Content-Type": "application/json"}
                )
                if resp.status_code not in (200, 201):
                    raise Exception(f"Create dataset failed: {resp.status_code} {resp.text}")
                data = resp.json()
                dataset_id = data.get("id")
                return data

            await run_step(step, do_create_dataset())
            report.add_result(step)
            log_response(step)
    else:
        step.status = "FAIL"
        step.error = "No dataset_id from previous step"
        report.add_result(step)
        log_response(step)

    # --- Step 5: 获取数据集详情 ---
    step = make_step("5. GET /api/datasets/{id} (获取数据集详情)")
    if dataset_id:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            async def do_get_dataset():
                resp = await client.get(
                    f"{base_url}/api/datasets/{dataset_id}",
                    headers=headers
                )
                if resp.status_code != 200:
                    raise Exception(f"Get dataset failed: {resp.status_code} {resp.text}")
                return resp.json()

            await run_step(step, do_get_dataset())
            report.add_result(step)
            log_response(step)
    else:
        step.status = "FAIL"
        step.error = "No dataset_id from previous step"
        report.add_result(step)
        log_response(step)

    # --- Step 6: 创建实验 ---
    step = make_step("6. POST /api/experiments/ (创建实验)")
    experiment_id: Optional[str] = None
    if dataset_id:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            async def do_create_experiment():
                nonlocal experiment_id
                payload: Dict[str, Any] = {
                    "name": f"smoke_test_experiment_{uuid.uuid4().hex[:8]}",
                    "description": "Smoke test experiment",
                    "dataset_id": dataset_id,
                    "config": {
                        "xgboost_params": {
                            "n_estimators": 10,
                            "max_depth": 3,
                            "learning_rate": 0.1,
                            "subsample": 0.8,
                            "colsample_bytree": 0.8,
                        },
                        "early_stopping_rounds": 5,
                        "validation_split": 0.2,
                        "random_state": 42,
                    },
                    "tags": ["smoke-test", "auto-generated"]
                }
                resp = await client.post(
                    f"{base_url}/api/experiments/",
                    json=payload,
                    headers={**headers, "Content-Type": "application/json"}
                )
                if resp.status_code not in (200, 201):
                    raise Exception(f"Create experiment failed: {resp.status_code} {resp.text}")
                data = resp.json()
                experiment_id = data.get("id")
                return data

            await run_step(step, do_create_experiment())
            report.add_result(step)
            log_response(step)
    else:
        step.status = "FAIL"
        step.error = "No dataset_id from previous step"
        report.add_result(step)
        log_response(step)

    # --- Step 7: 启动训练 (POST /api/experiments/{id}/start) ---
    step = make_step("7. POST /api/experiments/{id}/start (提交训练)")
    training_started = False
    if experiment_id:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            async def do_start_training():
                nonlocal training_started
                resp = await client.post(
                    f"{base_url}/api/experiments/{experiment_id}/start",
                    headers=headers
                )
                if resp.status_code != 200:
                    raise Exception(f"Start training failed: {resp.status_code} {resp.text}")
                data = resp.json()
                training_started = True
                return data

            await run_step(step, do_start_training())
            report.add_result(step)
            log_response(step)
    else:
        step.status = "FAIL"
        step.error = "No experiment_id from previous step"
        report.add_result(step)
        log_response(step)

    # --- Step 8: GET /api/training/status (查看队列) ---
    step = make_step("8. GET /api/training/status (查看训练队列)")
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        async def do_get_status():
            resp = await client.get(
                f"{base_url}/api/training/status",
                headers=headers
            )
            if resp.status_code != 200:
                raise Exception(f"Get status failed: {resp.status_code} {resp.text}")
            return resp.json()

        await run_step(step, do_get_status())
        report.add_result(step)
        log_response(step)

    # --- Step 9: 轮询等待训练完成 ---
    step = make_step("9. 轮询等待训练完成 (GET /api/training/{id}/status)")
    training_completed = False
    if experiment_id:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            async def do_poll_training():
                nonlocal training_completed
                start_time = time.time()
                while time.time() - start_time < TRAINING_POLL_TIMEOUT:
                    resp = await client.get(
                        f"{base_url}/api/training/{experiment_id}/status",
                        headers=headers
                    )
                    if resp.status_code != 200:
                        raise Exception(f"Poll status failed: {resp.status_code} {resp.text}")
                    data = resp.json()
                    status = data.get("status", "")
                    elapsed = time.time() - start_time
                    print(f"      训练状态: {status} (已等待 {elapsed:.0f}s)")

                    if status in ("completed", "failed", "cancelled"):
                        training_completed = True
                        return data

                    await asyncio.sleep(TRAINING_POLL_INTERVAL)

                raise Exception(f"Training timeout after {TRAINING_POLL_TIMEOUT}s")

            await run_step(step, do_poll_training())
            report.add_result(step)
            log_response(step)
    else:
        step.status = "FAIL"
        step.error = "No experiment_id from previous step"
        report.add_result(step)
        log_response(step)

    # --- Step 10: GET /api/results/{id} (获取结果) ---
    step = make_step("10. GET /api/results/{id} (获取训练结果)")
    result_data: Optional[Dict[str, Any]] = None
    if experiment_id:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            async def do_get_result():
                nonlocal result_data
                resp = await client.get(
                    f"{base_url}/api/results/{experiment_id}",
                    headers=headers
                )
                if resp.status_code != 200:
                    raise Exception(f"Get result failed: {resp.status_code} {resp.text}")
                data = resp.json()
                result_data = data
                return data

            await run_step(step, do_get_result())
            report.add_result(step)
            log_response(step)
    else:
        step.status = "FAIL"
        step.error = "No experiment_id from previous step"
        report.add_result(step)
        log_response(step)

    # --- Step 11: GET /api/results/{id}/feature-importance (特征重要性) ---
    step = make_step("11. GET /api/results/{id}/feature-importance (特征重要性)")
    if experiment_id:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            async def do_get_feature_importance():
                resp = await client.get(
                    f"{base_url}/api/results/{experiment_id}/feature-importance",
                    headers=headers
                )
                if resp.status_code != 200:
                    raise Exception(f"Get feature importance failed: {resp.status_code} {resp.text}")
                return resp.json()

            await run_step(step, do_get_feature_importance())
            report.add_result(step)
            log_response(step)
    else:
        step.status = "FAIL"
        step.error = "No experiment_id from previous step"
        report.add_result(step)
        log_response(step)

    # --- Step 12: POST /api/results/compare (对比实验) ---
    step = make_step("12. POST /api/results/compare (对比实验)")
    if experiment_id:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            async def do_compare():
                # 对比实验至少需要 2 个实验 ID，这里用同一个实验 ID 两次来测试端点
                # 实际使用中应该传入不同的实验 ID
                resp = await client.post(
                    f"{base_url}/api/results/compare",
                    json=[experiment_id, experiment_id],
                    headers={**headers, "Content-Type": "application/json"}
                )
                if resp.status_code != 200:
                    raise Exception(f"Compare failed: {resp.status_code} {resp.text}")
                return resp.json()

            await run_step(step, do_compare())
            report.add_result(step)
            log_response(step)
    else:
        step.status = "FAIL"
        step.error = "No experiment_id from previous step"
        report.add_result(step)
        log_response(step)

    # --- Step 13: POST /api/auth/logout (登出) ---
    step = make_step("13. POST /api/auth/logout (登出)")
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        async def do_logout():
            resp = await client.post(
                f"{base_url}/api/auth/logout",
                headers=headers
            )
            if resp.status_code != 200:
                raise Exception(f"Logout failed: {resp.status_code} {resp.text}")
            return resp.json()

        await run_step(step, do_logout())
        report.add_result(step)
        log_response(step)


# ========== 主入口 ==========

def main():
    parser = argparse.ArgumentParser(description="API 集成冒烟测试脚本")
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000",
        help="API 基础 URL (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--username",
        default=_DEFAULT_USERNAME,
        help=f"登录用户名 (default: {_DEFAULT_USERNAME})"
    )
    parser.add_argument(
        "--password",
        default=_DEFAULT_PASSWORD,
        help=f"登录密码 (default: {_DEFAULT_PASSWORD})"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("API 集成冒烟测试")
    print("=" * 60)
    print(f"API URL: {args.api_url}")
    print(f"Username: {args.username}")
    print(f"开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    overall_start = time.time()
    report = TestReport()

    # 运行冒烟测试
    try:
        asyncio.run(run_smoke_test(args.api_url, report, args.username, args.password))
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"\n测试执行异常: {e}")

    overall_duration = time.time() - overall_start

    # 打印报告
    report.print_summary()
    print(f"总耗时: {overall_duration:.2f}s")

    # 退出码
    if report.all_passed:
        print("\n退出码: 0 (全部通过)")
        sys.exit(0)
    else:
        print(f"\n退出码: 1 ({report.failed} 个步骤失败)")
        sys.exit(1)


if __name__ == "__main__":
    main()