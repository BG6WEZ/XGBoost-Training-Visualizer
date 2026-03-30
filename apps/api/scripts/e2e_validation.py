"""
端到端验收脚本

执行完整的训练 -> 结果读取 -> 模型下载验证流程
"""

import asyncio
import httpx
import json
import os
import sys
import argparse
from datetime import datetime
from typing import Optional, Dict, Any

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
DATASET_ID = os.getenv("TEST_DATASET_ID", None)


class E2EResults:
    """端到端验收结果"""
    
    def __init__(self, data: Dict[str, Any]):
        self.success = data.get("success", False)
        self.experiment_id = data.get("experiment_id")
        self.steps = data.get("steps", {})
        self.error = data.get("error")
        self.duration_seconds = data.get("duration_seconds")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "experiment_id": self.experiment_id,
            "steps": self.steps,
            "error": self.error,
            "duration_seconds": self.duration_seconds,
        }


async def check_services(api_url: str) -> Dict[str, Any]:
    """
    检查服务是否可用
    
    健康检查端点说明：
    - /health: 基础健康检查（无前缀）
    - /ready: 就绪检查，包含数据库和存储状态（无前缀）
    - /live: 存活检查（无前缀）
    """
    results = {}
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{api_url}/health")
            if response.status_code == 200:
                data = response.json()
                results["api"] = {
                    "status": "healthy",
                    "version": data.get("version", "unknown"),
                    "service": data.get("service", "unknown")
                }
            else:
                results["api"] = {"status": "unhealthy", "error": f"API returned {response.status_code}"}
        except httpx.ConnectError as e:
            results["api"] = {"status": "unreachable", "error": f"Connection refused: {e}"}
        except Exception as e:
            results["api"] = {"status": "error", "error": str(e)}
        
        try:
            response = await client.get(f"{api_url}/ready")
            if response.status_code == 200:
                data = response.json()
                checks = data.get("checks", {})
                results["readiness"] = {
                    "status": data.get("status", "unknown"),
                    "database": checks.get("database", {}).get("status", "unknown"),
                    "storage": checks.get("storage", {}).get("status", "unknown"),
                }
            else:
                results["readiness"] = {"status": "not_ready", "error": f"Ready check returned {response.status_code}"}
        except Exception as e:
            results["readiness"] = {"status": "error", "error": str(e)}
        
        try:
            response = await client.get(f"{api_url}/api/training/status")
            if response.status_code == 200:
                data = response.json()
                worker_status = data.get("worker_status", "unknown")
                redis_status = data.get("redis_status", "unknown")
                queue_length = data.get("queue_length", 0)
                
                results["worker"] = {
                    "status": worker_status,
                    "redis_status": redis_status,
                    "queue_length": queue_length
                }
            elif response.status_code == 404:
                results["worker"] = {"status": "not_available", "note": "Training status endpoint not found"}
            else:
                results["worker"] = {"status": "unhealthy", "error": f"Worker returned {response.status_code}"}
        except Exception as e:
            results["worker"] = {"status": "error", "error": str(e)}
    
    return results


async def get_dataset_id(client: httpx.AsyncClient, api_url: str) -> Optional[str]:
    """获取数据集ID，优先选择适合测试的数据集"""
    global DATASET_ID
    
    if DATASET_ID:
        return DATASET_ID
    
    response = await client.get(f"{api_url}/api/datasets/")
    
    if response.status_code == 200:
        datasets = response.json()
        
        # 优先选择 "Demo Test Dataset" 或 "Smoke Test Dataset"
        for ds in datasets:
            if "Demo Test" in ds.get("name", "") or "Smoke Test" in ds.get("name", ""):
                DATASET_ID = ds["id"]
                return DATASET_ID
        
        # 否则选择第一个数据集
        if datasets:
            DATASET_ID = datasets[0]["id"]
            return DATASET_ID
    
    dataset_data = {
        "name": f"E2E Test Dataset {datetime.now().isoformat()}",
        "description": "Auto-created for E2E validation",
        "files": [
            {
                "file_path": "dataset/building_energy_data_extended.csv",
                "file_name": "building_energy_data_extended.csv",
                "role": "primary",
                "row_count": 7200,
                "column_count": 14,
                "file_size": 1024000
            }
        ]
    }
    
    response = await client.post(
        f"{api_url}/api/datasets/",
        json=dataset_data
    )
    
    if response.status_code not in [200, 201]:
        raise Exception(f"Failed to create dataset: status={response.status_code}, body={response.text[:500]}")
    
    DATASET_ID = response.json()["id"]
    return DATASET_ID


async def split_dataset(client: httpx.AsyncClient, api_url: str, dataset_id: str) -> Dict[str, Any]:
    """执行数据切分"""
    response = await client.post(
        f"{api_url}/api/datasets/{dataset_id}/split",
        json={
            "split_method": "random",
            "test_size": 0.2,
            "random_seed": 42
        }
    )
    
    if response.status_code not in [200, 201]:
        raise Exception(f"Failed to split dataset: status={response.status_code}, body={response.text[:500]}")
    
    return response.json()


async def create_experiment(client: httpx.AsyncClient, api_url: str, dataset_id: str) -> str:
    """
    创建实验
    
    注意：FastAPI 默认返回 200，而不是 201
    
    获取数据集详情以动态选择目标列
    """
    # 获取数据集详情
    response = await client.get(f"{api_url}/api/datasets/{dataset_id}")
    
    if response.status_code != 200:
        raise Exception(f"Failed to get dataset details: status={response.status_code}, body={response.text[:500]}")
    
    dataset_info = response.json()
    
    # columns_info 在 files[0].columns_info 中
    files = dataset_info.get("files", [])
    if not files:
        raise Exception("Dataset has no files")
    
    columns_info = files[0].get("columns_info", [])
    
    # 选择一个合适的目标列（优先选择数值列且无缺失值）
    target_column = None
    for col_info in columns_info:
        if col_info.get("is_numeric") and col_info.get("missing_count", 1) == 0:
            target_column = col_info.get("name")
            break
    
    if not target_column:
        # 如果没有无缺失值的数值列，选择第一个数值列
        for col_info in columns_info:
            if col_info.get("is_numeric"):
                target_column = col_info.get("name")
                break
    
    if not target_column:
        raise Exception("No suitable target column found in dataset")
    
    response = await client.post(
        f"{api_url}/api/experiments/",
        json={
            "name": f"E2E Validation Experiment {datetime.now().isoformat()}",
            "description": "Auto-created for E2E validation",
            "dataset_id": dataset_id,
            "target_column": target_column,
            "config": {
                "test_size": 0.2,
                "random_seed": 42,
                "xgboost_params": {
                    "n_estimators": 50,
                    "learning_rate": 0.1,
                    "max_depth": 4
                }
            }
        }
    )
    
    if response.status_code not in [200, 201]:
        raise Exception(f"Failed to create experiment: status={response.status_code}, body={response.text[:500]}")
    
    data = response.json()
    experiment_id = data.get("id")
    if not experiment_id:
        raise Exception(f"Experiment created but no ID returned: {json.dumps(data)[:500]}")
    
    return experiment_id


async def start_training(client: httpx.AsyncClient, api_url: str, experiment_id: str) -> Dict[str, Any]:
    """启动训练"""
    response = await client.post(
        f"{api_url}/api/experiments/{experiment_id}/start"
    )
    
    if response.status_code not in [200, 201]:
        raise Exception(f"Failed to start training: status={response.status_code}, body={response.text[:500]}")
    
    return response.json()


async def wait_for_completion(client: httpx.AsyncClient, api_url: str, experiment_id: str, timeout: int = 120) -> bool:
    """等待训练完成"""
    start_time = datetime.now()
    
    while True:
        elapsed = (datetime.now() - start_time).total_seconds()
        
        if elapsed > timeout:
            raise TimeoutError(f"Training did not complete within {timeout} seconds")
        
        response = await client.get(
            f"{api_url}/api/experiments/{experiment_id}"
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to get experiment status: status={response.status_code}, body={response.text[:500]}")
        
        data = response.json()
        status = data.get("status")
        
        if status == "completed":
            return True
        
        if status == "failed":
            error_msg = data.get("error_message", "Unknown error")
            raise Exception(f"Training failed: {error_msg}")
        
        await asyncio.sleep(2)


async def get_results(client: httpx.AsyncClient, api_url: str, experiment_id: str) -> Dict[str, Any]:
    """获取实验结果"""
    response = await client.get(
        f"{api_url}/api/results/{experiment_id}"
    )
    
    if response.status_code != 200:
        raise Exception(f"Failed to get results: status={response.status_code}, body={response.text[:500]}")
    
    return response.json()


async def download_model(client: httpx.AsyncClient, api_url: str, experiment_id: str) -> bytes:
    """下载模型"""
    response = await client.get(
        f"{api_url}/api/results/{experiment_id}/download-model"
    )
    
    if response.status_code != 200:
        raise Exception(f"Failed to download model: status={response.status_code}, body={response.text[:500]}")
    
    return response.content


async def run_e2e_validation(api_url: str, timeout: int = 120, output_json: bool = False) -> E2EResults:
    """运行端到端验证"""
    start_time = datetime.now()
    results = E2EResults({"success": False, "steps": {}})
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            service_status = await check_services(api_url)
            results.steps["service_check"] = service_status
            
            api_status = service_status.get("api", {}).get("status")
            if api_status == "unreachable":
                results.success = False
                results.error = f"API service unreachable: {service_status.get('api', {}).get('error', 'Unknown')}"
                results.duration_seconds = (datetime.now() - start_time).total_seconds()
                return results
            
            if api_status not in ["healthy", "error"]:
                results.success = False
                results.error = f"API service not healthy: {api_status}"
                results.duration_seconds = (datetime.now() - start_time).total_seconds()
                return results
            
            # 队列健康前置检查
            worker_status = service_status.get("worker", {})
            queue_length = worker_status.get("queue_length", 0)
            if queue_length > 0:
                results.steps["queue_check"] = {"queue_length": queue_length, "status": "waiting"}
                max_wait = 60
                wait_start = datetime.now()
                while queue_length > 0:
                    elapsed = (datetime.now() - wait_start).total_seconds()
                    if elapsed > max_wait:
                        results.success = False
                        results.error = f"Queue not empty after {max_wait}s, queue_length={queue_length}"
                        results.duration_seconds = (datetime.now() - start_time).total_seconds()
                        return results
                    await asyncio.sleep(3)
                    status_resp = await client.get(f"{api_url}/api/training/status")
                    if status_resp.status_code == 200:
                        queue_length = status_resp.json().get("queue_length", 0)
                results.steps["queue_check"] = {"status": "cleared", "wait_seconds": (datetime.now() - wait_start).total_seconds()}
            
            dataset_id = await get_dataset_id(client, api_url)
            if not dataset_id:
                raise Exception("Failed to get dataset ID")
            
            results.steps["dataset_id"] = dataset_id
            
            split_result = await split_dataset(client, api_url, dataset_id)
            results.steps["split"] = {"status": "success", "subsets": len(split_result.get("subsets", []))}
            
            experiment_id = await create_experiment(client, api_url, dataset_id)
            results.steps["create_experiment"] = {"status": "success", "experiment_id": experiment_id}
            
            start_result = await start_training(client, api_url, experiment_id)
            results.steps["start_training"] = {"status": "success", "queue_position": start_result.get("queue_position")}
            
            completion = await wait_for_completion(client, api_url, experiment_id, timeout)
            results.steps["wait_for_completion"] = {"status": "success"}
            
            results_data = await get_results(client, api_url, experiment_id)
            results.steps["get_results"] = {
                "status": "success",
                "experiment_status": results_data.get("status"),
                "has_model": results_data.get("model") is not None
            }
            
            if not results_data.get("model"):
                results.success = False
                results.error = "Model info not found in results"
                results.duration_seconds = (datetime.now() - start_time).total_seconds()
                return results
            
            model_content = await download_model(client, api_url, experiment_id)
            results.steps["download_model"] = {"status": "success", "size_bytes": len(model_content)}
            
            if not model_content:
                results.success = False
                results.error = "Model content is empty"
                results.duration_seconds = (datetime.now() - start_time).total_seconds()
                return results
            
            try:
                model_data = json.loads(model_content)
                
                # 检测模型类型
                # 优先检查显式的 model_type 字段
                model_type = model_data.get("model_type")
                
                # 如果没有显式的 model_type，检测 XGBoost 原生 JSON 格式
                # XGBoost 原生 JSON 顶层字段为: learner, version
                if model_type is None:
                    if "learner" in model_data and "version" in model_data:
                        model_type = "xgboost"
                    else:
                        model_type = "unknown"
                
                model_format = model_data.get("format", "json")
                
                # 检查 feature_names（可能在顶层或 learner 对象中）
                has_feature_names = "feature_names" in model_data
                if not has_feature_names and "learner" in model_data:
                    learner = model_data.get("learner", {})
                    has_feature_names = "feature_names" in learner
                
                # 检查 target（可能在顶层或 learner 对象中）
                has_target = "target" in model_data
                if not has_target and "learner" in model_data:
                    learner = model_data.get("learner", {})
                    has_target = "target" in learner
                
                validation_result = {
                    "status": "success",
                    "model_type": model_type,
                    "format": model_format,
                    "size_bytes": len(model_content),
                    "has_feature_names": has_feature_names,
                    "has_target": has_target,
                }
                
                if model_type == "xgboost":
                    validation_result["validation_level"] = "full"
                    validation_result["message"] = "XGBoost model validated successfully"
                elif model_type == "unknown":
                    validation_result["validation_level"] = "partial"
                    validation_result["message"] = "Model type not specified, but content is valid JSON"
                else:
                    validation_result["validation_level"] = "full"
                    validation_result["message"] = f"{model_type} model validated successfully"
                
                results.steps["model_validation"] = validation_result
            except json.JSONDecodeError:
                results.success = False
                results.error = "Model content is not valid JSON"
                results.duration_seconds = (datetime.now() - start_time).total_seconds()
                return results
            
            results.success = True
            results.experiment_id = experiment_id
            results.duration_seconds = (datetime.now() - start_time).total_seconds()
    
    except Exception as e:
        results.success = False
        results.error = str(e)
        results.duration_seconds = (datetime.now() - start_time).total_seconds()
    
    return results


async def async_main(api_url: str, timeout: int, output_json: bool) -> int:
    """异步主函数"""
    if output_json:
        results = await run_e2e_validation(api_url, timeout, output_json)
        print(json.dumps(results.to_dict(), indent=2, ensure_ascii=False))
        return 0 if results.success else 1
    
    print("=" * 60)
    print("XGBoost Training Visualizer - E2E Validation")
    print("=" * 60)
    
    print(f"\n[配置信息]")
    print(f"  API URL: {api_url}")
    print(f"  Timeout: {timeout}s")
    
    print("\n[前置条件检查]")
    service_status = await check_services(api_url)
    
    api_healthy = service_status.get("api", {}).get("status") == "healthy"
    readiness = service_status.get("readiness", {}).get("status")
    
    for service, status in service_status.items():
        if status.get("status") in ["healthy", "ready"]:
            print(f"  ✅ {service}: {status.get('status')}")
        elif status.get("status") == "not_available":
            print(f"  ⚠️  {service}: {status.get('status')} - {status.get('note', '')}")
        else:
            print(f"  ❌ {service}: {status.get('status')} - {status.get('error', 'Unknown')}")
    
    if not api_healthy:
        print("\n❌ API 服务不可用，请确保 API 服务正在运行")
        print("   启动命令: pnpm dev:api")
        return 1
    
    if readiness and readiness != "ready":
        print(f"\n⚠️  服务就绪状态: {readiness}")
        checks = service_status.get("readiness", {})
        if checks.get("database") != "ok":
            print("   数据库连接异常，请检查 PostgreSQL")
        if checks.get("storage") != "ok":
            print("   存储服务异常，请检查 WORKSPACE_DIR 配置")
    
    print("\n[端到端验证开始]")
    results = await run_e2e_validation(api_url, timeout, output_json)
    
    print("\n[验证结果]")
    if results.success:
        print(f"  ✅ 端到端验证通过")
        print(f"  实验ID: {results.experiment_id}")
        print(f"  总耗时: {results.duration_seconds:.2f} 秒")
        print("  步骤详情:")
        for step, status in results.steps.items():
            if isinstance(status, dict):
                step_status = status.get("status", "unknown")
                if step_status == "success":
                    print(f"    ✅ {step}: 通过")
                else:
                    print(f"    - {step}: {json.dumps(status, ensure_ascii=False)}")
            else:
                print(f"    - {step}: {status}")
    else:
        print(f"  ❌ 端到端验证失败")
        print(f"  错误: {results.error}")
        print(f"  总耗时: {results.duration_seconds:.2f} 秒")
        if results.steps:
            print("  已完成步骤:")
            for step, status in results.steps.items():
                print(f"    - {step}: {json.dumps(status, ensure_ascii=False) if isinstance(status, dict) else status}")
    
    print("\n" + "=" * 60)
    print("XGBoost Training Visualizer - E2E Validation Complete")
    print("=" * 60)
    
    return 0 if results.success else 1


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="XGBoost Training Visualizer E2E Validation")
    parser.add_argument("--api-url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--dataset-id", default=None, help="Dataset ID (optional)")
    parser.add_argument("--timeout", default=120, type=int, help="Timeout in seconds")
    parser.add_argument("--output", choices=["text", "json"], default="text", help="Output format")
    
    args = parser.parse_args()
    
    global DATASET_ID
    if args.dataset_id:
        DATASET_ID = args.dataset_id
    
    output_json = args.output == "json"
    
    return asyncio.run(async_main(args.api_url, args.timeout, output_json))


if __name__ == "__main__":
    sys.exit(main())
