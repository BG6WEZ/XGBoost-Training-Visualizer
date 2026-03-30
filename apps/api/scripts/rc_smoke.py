"""
RC Smoke - MVP 最终验收脚本

串联检查：
1. 服务健康检查（API/readiness/worker）
2. M1 资产链路最小验证（目录资产扫描 + 多文件数据集存在）
3. 结果链路验证（执行一次 e2e_validation.py --output json）

退出码语义：全部通过返回 0，否则非 0
"""
import asyncio
import httpx
import json
import sys
import subprocess
from datetime import datetime
from typing import Dict, Any, List


class RCSmokeResult:
    """RC Smoke 验收结果"""
    
    def __init__(self):
        self.success = True
        self.checks: List[Dict[str, Any]] = []
        self.timestamp = datetime.now().isoformat()
        self.duration_seconds = 0.0
    
    def add_check(self, name: str, status: bool, details: Dict[str, Any] = None, error: str = None):
        """添加检查项"""
        check = {
            "name": name,
            "status": "passed" if status else "failed",
            "timestamp": datetime.now().isoformat()
        }
        if details:
            check["details"] = details
        if error:
            check["error"] = error
        self.checks.append(check)
        if not status:
            self.success = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "timestamp": self.timestamp,
            "duration_seconds": self.duration_seconds,
            "checks": self.checks
        }


async def check_service_health(api_url: str, result: RCSmokeResult):
    """检查服务健康状态"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        # API health
        try:
            r = await client.get(f"{api_url}/health")
            if r.status_code == 200:
                data = r.json()
                result.add_check(
                    "api_health",
                    True,
                    {"status": data.get("status"), "version": data.get("version")}
                )
            else:
                result.add_check("api_health", False, error=f"HTTP {r.status_code}")
        except Exception as e:
            result.add_check("api_health", False, error=str(e))
        
        # Readiness
        try:
            r = await client.get(f"{api_url}/ready")
            if r.status_code == 200:
                data = r.json()
                checks = data.get("checks", {})
                result.add_check(
                    "readiness",
                    data.get("status") == "ready",
                    {
                        "status": data.get("status"),
                        "database": checks.get("database", {}).get("status"),
                        "storage": checks.get("storage", {}).get("status")
                    }
                )
            else:
                result.add_check("readiness", False, error=f"HTTP {r.status_code}")
        except Exception as e:
            result.add_check("readiness", False, error=str(e))
        
        # Worker status
        try:
            r = await client.get(f"{api_url}/api/training/status")
            if r.status_code == 200:
                data = r.json()
                result.add_check(
                    "worker_status",
                    data.get("worker_status") == "healthy",
                    {
                        "worker_status": data.get("worker_status"),
                        "redis_status": data.get("redis_status"),
                        "queue_length": data.get("queue_length")
                    }
                )
            else:
                result.add_check("worker_status", False, error=f"HTTP {r.status_code}")
        except Exception as e:
            result.add_check("worker_status", False, error=str(e))


async def check_m1_assets(api_url: str, result: RCSmokeResult):
    """检查 M1 资产链路"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 扫描资产
        try:
            r = await client.get(f"{api_url}/api/assets/scan")
            if r.status_code != 200:
                result.add_check("m1_asset_scan", False, error=f"HTTP {r.status_code}")
                return
            
            data = r.json()
            assets = data.get("assets", [])
            
            # 检查目录型资产
            dir_assets = [a for a in assets if a.get("path_type") == "directory"]
            if len(dir_assets) == 0:
                result.add_check("m1_directory_assets", False, error="No directory assets found")
            else:
                result.add_check(
                    "m1_directory_assets",
                    True,
                    {"count": len(dir_assets), "examples": [a["name"] for a in dir_assets[:3]]}
                )
        except Exception as e:
            result.add_check("m1_asset_scan", False, error=str(e))
            return
        
        # 检查多文件数据集
        try:
            r = await client.get(f"{api_url}/api/datasets/")
            if r.status_code != 200:
                result.add_check("m1_multi_file_datasets", False, error=f"HTTP {r.status_code}")
                return
            
            datasets = r.json()
            multi_file_count = 0
            for ds in datasets:
                detail_r = await client.get(f"{api_url}/api/datasets/{ds['id']}")
                if detail_r.status_code == 200:
                    detail = detail_r.json()
                    if len(detail.get("files", [])) > 1:
                        multi_file_count += 1
            
            if multi_file_count > 0:
                result.add_check(
                    "m1_multi_file_datasets",
                    True,
                    {"count": multi_file_count}
                )
            else:
                result.add_check("m1_multi_file_datasets", False, error="No multi-file datasets found")
        except Exception as e:
            result.add_check("m1_multi_file_datasets", False, error=str(e))


def run_e2e_validation(result: RCSmokeResult):
    """运行 e2e 验证"""
    try:
        proc = subprocess.run(
            [sys.executable, "scripts/e2e_validation.py", "--output", "json", "--timeout", "120"],
            capture_output=True,
            text=True,
            timeout=180
        )
        
        if proc.returncode == 0:
            try:
                data = json.loads(proc.stdout)
                result.add_check(
                    "e2e_validation",
                    data.get("success", False),
                    {
                        "experiment_id": data.get("experiment_id"),
                        "duration_seconds": data.get("duration_seconds")
                    },
                    data.get("error")
                )
            except json.JSONDecodeError:
                result.add_check("e2e_validation", False, error="Invalid JSON output")
        else:
            result.add_check("e2e_validation", False, error=proc.stderr or f"Exit code {proc.returncode}")
    except subprocess.TimeoutExpired:
        result.add_check("e2e_validation", False, error="Timeout after 180s")
    except Exception as e:
        result.add_check("e2e_validation", False, error=str(e))


async def run_rc_smoke(api_url: str = "http://localhost:8000") -> RCSmokeResult:
    """运行 RC Smoke 验收"""
    start_time = datetime.now()
    result = RCSmokeResult()
    
    print("=" * 60)
    print("RC Smoke - MVP 最终验收")
    print("=" * 60)
    
    # 1. 服务健康检查
    print("\n[1/3] 服务健康检查...")
    await check_service_health(api_url, result)
    
    # 2. M1 资产链路检查
    print("[2/3] M1 资产链路检查...")
    await check_m1_assets(api_url, result)
    
    # 3. e2e 验证
    print("[3/3] e2e 验证...")
    run_e2e_validation(result)
    
    result.duration_seconds = (datetime.now() - start_time).total_seconds()
    
    return result


def main():
    """主入口"""
    result = asyncio.run(run_rc_smoke())
    
    print("\n" + "=" * 60)
    print("RC Smoke 结果")
    print("=" * 60)
    
    for check in result.checks:
        status_icon = "OK" if check["status"] == "passed" else "FAIL"
        print(f"  [{status_icon}] {check['name']}: {check['status']}")
        if "error" in check:
            print(f"       错误: {check['error']}")
        if "details" in check:
            print(f"       详情: {json.dumps(check['details'], ensure_ascii=False)}")
    
    print(f"\n总耗时: {result.duration_seconds:.2f}s")
    print(f"最终结果: {'ALL PASSED' if result.success else 'FAILED'}")
    
    print("\n" + "=" * 60)
    print("JSON 输出")
    print("=" * 60)
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    
    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())
