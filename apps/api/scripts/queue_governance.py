"""
队列治理脚本

功能：
1. 队列长度观测
2. 超阈值处理策略
3. 积压任务清理

退出码语义：
- 0: 队列正常
- 1: 队列有积压但已处理
- 2: 队列积压无法处理
"""
import httpx
import sys
import json
import time
from datetime import datetime

API_URL = "http://localhost:8000"
THRESHOLD = 5
MAX_WAIT = 60


def get_queue_status():
    r = httpx.get(f"{API_URL}/api/training/status", timeout=10)
    if r.status_code != 200:
        raise Exception(f"API error: {r.status_code}")
    return r.json()


def get_queued_experiments():
    r = httpx.get(f"{API_URL}/api/experiments/", timeout=30)
    if r.status_code != 200:
        raise Exception(f"API error: {r.status_code}")
    experiments = r.json()
    return [e for e in experiments if e.get("status") == "queued"]


def wait_for_queue_drain(max_wait=MAX_WAIT):
    start = datetime.now()
    while True:
        elapsed = (datetime.now() - start).total_seconds()
        if elapsed > max_wait:
            return False
        status = get_queue_status()
        queue_length = status.get("queue_length", 0)
        if queue_length == 0:
            return True
        print(f"  队列长度: {queue_length}, 等待中... ({elapsed:.0f}s)")
        time.sleep(5)


def main():
    print("=" * 60)
    print("队列治理检查")
    print("=" * 60)
    print(f"时间: {datetime.now().isoformat()}")
    print(f"阈值: {THRESHOLD}")
    print()
    
    print("[1/3] 队列状态观测...")
    try:
        status = get_queue_status()
        queue_length = status.get("queue_length", 0)
        worker_status = status.get("worker_status", "unknown")
        
        print(f"  Worker 状态: {worker_status}")
        print(f"  队列长度: {queue_length}")
    except Exception as e:
        print(f"  [ERROR] {e}")
        return 2
    
    print("\n[2/3] 阈值检查...")
    if queue_length == 0:
        print("  [OK] 队列为空")
        print("\n" + "=" * 60)
        print("结论: 队列正常，无需处理")
        print("=" * 60)
        return 0
    
    if queue_length <= THRESHOLD:
        print(f"  [INFO] 队列长度 {queue_length} <= 阈值 {THRESHOLD}")
    else:
        print(f"  [WARN] 队列长度 {queue_length} > 阈值 {THRESHOLD}")
    
    print("\n[3/3] Worker 检查...")
    if worker_status != "healthy":
        print("  [ERROR] Worker 不在线，无法消费队列")
        print("\n建议: 启动 Worker")
        print("  Windows: scripts\\start-local-worker.bat")
        print("  Unix:    ./scripts/start-local-worker.sh")
        return 2
    
    print("  [OK] Worker 在线")
    
    print("\n等待队列消费...")
    if wait_for_queue_drain():
        print("  [OK] 队列已清空")
        print("\n" + "=" * 60)
        print("结论: 队列积压已处理")
        print("=" * 60)
        return 1
    else:
        print("  [ERROR] 队列消费超时")
        print("\n建议: 检查 Worker 日志或手动清理")
        
        queued = get_queued_experiments()
        if queued:
            print(f"\n排队实验 ({len(queued)} 个):")
            for e in queued[:5]:
                print(f"  - {e.get('id')}: {e.get('name', 'N/A')}")
        
        return 2


if __name__ == "__main__":
    exit_code = main()
    
    print("\n" + "=" * 60)
    print("JSON 输出")
    print("=" * 60)
    
    try:
        status = get_queue_status()
        result = {
            "timestamp": datetime.now().isoformat(),
            "exit_code": exit_code,
            "queue_length": status.get("queue_length", -1),
            "worker_status": status.get("worker_status", "unknown"),
            "threshold": THRESHOLD,
            "conclusion": ["正常", "积压已处理", "无法处理"][exit_code] if exit_code <= 2 else "未知"
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False))
    
    sys.exit(exit_code)
