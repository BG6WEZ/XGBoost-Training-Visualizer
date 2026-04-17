#!/usr/bin/env python
"""
性能基线测试脚本

对 5 个关键端点执行并发请求，输出 P95、错误率、5xx 等指标。

用法:
    python scripts/benchmark.py --base-url http://localhost:8000
"""

import asyncio
import argparse
import time
import json
import os
import sys
import statistics
from dataclasses import dataclass, field
from typing import Optional

try:
    import httpx
except ImportError:
    print("ERROR: httpx is not installed. Please run: pip install httpx")
    sys.exit(1)


# ========== 配置 ==========

_DEFAULT_USERNAME = "admin"
_DEFAULT_PASSWORD = "admin123"

# 端点定义
ENDPOINTS = [
    {"name": "/health", "method": "GET", "concurrency": 50, "target_p95_ms": 50, "path": "/health"},
    {"name": "/api/auth/login", "method": "POST", "concurrency": 10, "target_p95_ms": 500, "path": "/api/auth/login"},
    {"name": "/api/datasets/", "method": "GET", "concurrency": 20, "target_p95_ms": 200, "path": "/api/datasets/"},
    {"name": "/api/experiments/", "method": "GET", "concurrency": 20, "target_p95_ms": 200, "path": "/api/experiments/"},
    {"name": "/api/datasets/upload (1MB CSV)", "method": "POST", "concurrency": 5, "target_p95_ms": 3000, "path": "/api/datasets/upload"},
]

REQUESTS_PER_CONCURRENT = 10  # 每个并发槽发送的请求数


# ========== 数据结构 ==========

@dataclass
class RequestResult:
    status_code: int = 0
    latency_ms: float = 0.0
    error: Optional[str] = None


@dataclass
class EndpointResult:
    name: str = ""
    total: int = 0
    success: int = 0
    failed: int = 0
    error_rate: float = 0.0
    avg_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    max_latency_ms: float = 0.0
    min_latency_ms: float = 0.0
    target_p95_ms: float = 0.0
    meets_target: bool = False
    status_5xx_count: int = 0
    errors: list = field(default_factory=list)
    latencies: list = field(default_factory=list)


# ========== 辅助函数 ==========

def _generate_1mb_csv(filepath: str) -> str:
    """生成约 1MB 的 CSV 文件"""
    import csv
    import uuid

    # 每行约 100 字节，需要约 10000 行
    rows_needed = 10000
    cols = 10

    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        # 写表头
        writer.writerow([f"col_{i}" for i in range(cols)])
        # 写数据行
        for _ in range(rows_needed):
            writer.writerow([f"val_{uuid.uuid4().hex[:8]}" for _ in range(cols)])

    return filepath


async def run_single_request(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    headers: dict = None,
    body: dict = None,
    file_path: str = None
) -> RequestResult:
    """执行单个请求并记录延迟"""
    result = RequestResult()
    start = time.monotonic()
    try:
        if method == "GET":
            resp = await client.get(url, headers=headers)
        elif method == "POST":
            if file_path:
                with open(file_path, 'rb') as f:
                    files = {"file": ("benchmark_1mb.csv", f, "text/csv")}
                    resp = await client.post(url, files=files, headers=headers)
            elif body:
                resp = await client.post(url, json=body, headers=headers)
            else:
                resp = await client.post(url, headers=headers)
        else:
            result.error = f"Unsupported method: {method}"
            return result

        result.status_code = resp.status_code
        result.latency_ms = (time.monotonic() - start) * 1000
    except httpx.ConnectTimeout:
        result.error = "ConnectTimeout"
        result.latency_ms = (time.monotonic() - start) * 1000
    except httpx.ReadTimeout:
        result.error = "ReadTimeout"
        result.latency_ms = (time.monotonic() - start) * 1000
    except httpx.RequestError as e:
        result.error = str(e)[:200]
        result.latency_ms = (time.monotonic() - start) * 1000
    except Exception as e:
        result.error = str(e)[:200]
        result.latency_ms = (time.monotonic() - start) * 1000

    return result


async def _semaphore_request(client, method, url, headers, body, file_path, sem):
    """使用信号量限制并发的请求。"""
    async with sem:
        return await run_single_request(client, method, url, headers, body, file_path)

async def run_endpoint_benchmark(
    base_url: str,
    endpoint: dict,
    auth_token: Optional[str] = None,
    file_path: Optional[str] = None
) -> EndpointResult:
    """对单个端点执行并发基准测试"""
    result = EndpointResult(
        name=endpoint["name"],
        target_p95_ms=endpoint["target_p95_ms"]
    )

    concurrency = endpoint["concurrency"]
    total_requests = concurrency * REQUESTS_PER_CONCURRENT
    result.total = total_requests

    headers = {}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"

    body = None
    if endpoint["path"] == "/api/auth/login":
        body = {"username": _DEFAULT_USERNAME, "password": _DEFAULT_PASSWORD}

    url = f"{base_url.rstrip('/')}{endpoint['path']}"

    # 使用连接池，复用连接
    limits = httpx.Limits(max_connections=concurrency, max_keepalive_connections=concurrency)
    timeout = httpx.Timeout(30.0, connect=10.0)

    async with httpx.AsyncClient(limits=limits, timeout=timeout) as client:
        # 使用信号量分批控制并发，避免同时创建大量连接
        sem = asyncio.Semaphore(concurrency)
        tasks = []
        for _ in range(total_requests):
            tasks.append(_semaphore_request(client, endpoint["method"], url, headers, body, file_path, sem))

        # 并发执行
        responses = await asyncio.gather(*tasks, return_exceptions=True)

    # 统计结果
    for resp in responses:
        if isinstance(resp, Exception):
            result.failed += 1
            result.errors.append(str(resp)[:200])
            continue

        if isinstance(resp, RequestResult):
            result.latencies.append(resp.latency_ms)
            if resp.error:
                result.failed += 1
                result.errors.append(resp.error)
            elif resp.status_code >= 500:
                result.failed += 1
                result.status_5xx_count += 1
                result.errors.append(f"HTTP {resp.status_code}")
            elif resp.status_code >= 200 and resp.status_code < 500:
                result.success += 1
            else:
                result.failed += 1
                result.errors.append(f"HTTP {resp.status_code}")

    # 计算统计指标
    if result.latencies:
        result.latencies.sort()
        result.avg_latency_ms = statistics.mean(result.latencies)
        result.max_latency_ms = max(result.latencies)
        result.min_latency_ms = min(result.latencies)
        # P95
        p95_index = int(len(result.latencies) * 0.95)
        result.p95_latency_ms = result.latencies[min(p95_index, len(result.latencies) - 1)]

    result.error_rate = (result.failed / result.total * 100) if result.total > 0 else 0
    result.meets_target = result.p95_latency_ms <= result.target_p95_ms

    return result


# ========== 主逻辑 ==========

async def run_benchmark(base_url: str):
    """执行完整基准测试"""
    print("=" * 70)
    print("性能基线测试")
    print("=" * 70)
    print(f"Base URL: {base_url}")
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Requests per concurrent slot: {REQUESTS_PER_CONCURRENT}")
    print("=" * 70)

    # 0. 确认 /ready
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(f"{base_url.rstrip('/')}/ready")
        if resp.status_code != 200:
            print(f"\n[FATAL] /ready 返回 {resp.status_code}，服务未就绪")
            return None
        print(f"\n[/ready] 200 OK - 服务就绪")

    # 0.5 Warmup: 发送少量预热请求，初始化连接池
    print("\n[Step 0.5] 发送预热请求...")
    warmup_count = 5
    async with httpx.AsyncClient(timeout=10.0) as client:
        for i in range(warmup_count):
            try:
                await client.get(f"{base_url.rstrip('/')}/health")
            except Exception:
                pass
    print(f"  预热完成（{warmup_count} 次 /health 请求）")

    # 1. 登录获取 token
    print("\n[Step 1] 获取认证 token...")
    auth_token = None
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            f"{base_url.rstrip('/')}/api/auth/login",
            json={"username": _DEFAULT_USERNAME, "password": _DEFAULT_PASSWORD}
        )
        if resp.status_code == 200:
            auth_token = resp.json().get("access_token")
            print(f"  Token 获取成功")
        else:
            print(f"  [WARN] 登录失败: {resp.status_code} {resp.text[:200]}")

    # 2. 准备 1MB CSV 文件
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, "benchmark_1mb.csv")
    print(f"\n[Step 2] 生成 1MB CSV 测试文件...")
    _generate_1mb_csv(csv_path)
    file_size = os.path.getsize(csv_path)
    print(f"  文件大小: {file_size / 1024 / 1024:.2f} MB")

    # 3. 执行基准测试
    all_results = []
    for ep in ENDPOINTS:
        ep_name = ep["name"]
        print(f"\n[Step 3] 测试 {ep_name} (并发={ep['concurrency']}, 目标 P95={ep['target_p95_ms']}ms)...")

        ep_result = await run_endpoint_benchmark(
            base_url=base_url,
            endpoint=ep,
            auth_token=auth_token if ep["path"] != "/api/auth/login" else None,
            file_path=csv_path if ep["path"] == "/api/datasets/upload" else None
        )

        all_results.append(ep_result)

        # 打印单端点结果
        status = "PASS" if ep_result.meets_target else "FAIL"
        print(f"  [{status}] {ep_name}")
        print(f"    总请求数: {ep_result.total}")
        print(f"    成功: {ep_result.success}, 失败: {ep_result.failed}")
        print(f"    错误率: {ep_result.error_rate:.2f}%")
        print(f"    平均延迟: {ep_result.avg_latency_ms:.2f}ms")
        print(f"    P95 延迟: {ep_result.p95_latency_ms:.2f}ms (目标: {ep_result.target_p95_ms}ms)")
        print(f"    最大延迟: {ep_result.max_latency_ms:.2f}ms")
        if ep_result.status_5xx_count > 0:
            print(f"    5xx 错误: {ep_result.status_5xx_count}")
        if ep_result.errors:
            unique_errors = list(set(ep_result.errors[:10]))
            print(f"    错误类型: {', '.join(unique_errors)}")

    # 4. 汇总报告
    print("\n" + "=" * 70)
    print("性能基线测试报告")
    print("=" * 70)

    # 端点汇总表
    print(f"\n{'端点':<40} {'总请求':>6} {'成功':>6} {'失败':>6} {'错误率':>8} {'P95/ms':>10} {'目标/ms':>10} {'达标':>4}")
    print("-" * 90)
    for r in all_results:
        print(f"{r.name:<40} {r.total:>6} {r.success:>6} {r.failed:>6} {r.error_rate:>7.2f}% {r.p95_latency_ms:>10.2f} {r.target_p95_ms:>10.0f} {'PASS' if r.meets_target else 'FAIL':>4}")

    # 5xx 统计
    total_5xx = sum(r.status_5xx_count for r in all_results)
    print(f"\n5xx 错误总计: {total_5xx}")

    # 整体通过率
    total_requests = sum(r.total for r in all_results)
    total_success = sum(r.success for r in all_results)
    overall_pass = all(r.meets_target for r in all_results)
    print(f"整体请求成功率: {total_success / total_requests * 100:.2f}%")
    print(f"全部端点达标: {'是' if overall_pass else '否'}")
    print("=" * 70)

    # 清理临时文件
    if os.path.exists(csv_path):
        os.remove(csv_path)

    return all_results


def main():
    parser = argparse.ArgumentParser(description="性能基线测试脚本")
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="API 基础 URL (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--requests-per-concurrent",
        type=int,
        default=10,
        help="每个并发槽的请求数 (default: 10)"
    )
    args = parser.parse_args()

    global REQUESTS_PER_CONCURRENT
    REQUESTS_PER_CONCURRENT = args.requests_per_concurrent

    try:
        results = asyncio.run(run_benchmark(args.base_url))
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n测试执行异常: {e}")
        sys.exit(1)

    if results is None:
        sys.exit(1)

    # 退出码：全部达标 exit 0，否则 exit 1
    all_pass = all(r.meets_target for r in results)
    if all_pass:
        print("\n退出码: 0 (全部达标)")
        sys.exit(0)
    else:
        print(f"\n退出码: 1 (部分端点未达标)")
        sys.exit(1)


if __name__ == "__main__":
    main()