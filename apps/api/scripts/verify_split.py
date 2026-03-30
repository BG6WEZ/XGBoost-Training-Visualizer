import httpx
import json

dataset_id = "4616e4d8-24c7-4e6c-8f30-e5ee909f204b"

print("=== 验证 split 功能 ===")

split_payload = {
    "dataset_id": dataset_id,
    "split_method": "random",
    "train_ratio": 0.8,
    "val_ratio": 0.1,
    "test_ratio": 0.1,
    "random_seed": 42
}

r = httpx.post(
    f'http://localhost:8000/api/datasets/{dataset_id}/split',
    json=split_payload,
    timeout=60
)

print(f"Split 状态码: {r.status_code}")

if r.status_code == 200:
    result = r.json()
    print(f"完整响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
    print("✅ Split 成功!")
else:
    print(f"Split 失败: {r.text}")
