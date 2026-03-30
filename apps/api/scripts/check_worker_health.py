"""
Worker 健康检查脚本

检查 Worker 状态和队列消费能力
"""
import httpx
import sys

API_URL = "http://localhost:8000"

def check_worker_health():
    """检查 Worker 健康状态"""
    print("=" * 60)
    print("Worker 健康检查")
    print("=" * 60)
    
    try:
        r = httpx.get(f"{API_URL}/api/training/status", timeout=10)
        if r.status_code != 200:
            print(f"[FAIL] API 返回 {r.status_code}")
            return False
        
        data = r.json()
        worker_status = data.get("worker_status", "unknown")
        redis_status = data.get("redis_status", "unknown")
        queue_length = data.get("queue_length", -1)
        active_experiments = data.get("active_experiments", 0)
        
        print(f"Worker 状态: {worker_status}")
        print(f"Redis 状态: {redis_status}")
        print(f"队列长度: {queue_length}")
        print(f"活跃实验: {active_experiments}")
        
        if worker_status == "healthy" and redis_status == "connected":
            print("\n[OK] Worker 健康检查通过")
            return True
        else:
            print("\n[FAIL] Worker 不健康")
            return False
            
    except httpx.ConnectError:
        print("[FAIL] API 服务不可达")
        return False
    except Exception as e:
        print(f"[FAIL] 检查失败: {e}")
        return False

if __name__ == "__main__":
    success = check_worker_health()
    sys.exit(0 if success else 1)
