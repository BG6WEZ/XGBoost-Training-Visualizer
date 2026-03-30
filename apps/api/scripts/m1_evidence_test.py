"""M1 证据补齐脚本"""
import httpx
import json

def test_folder_upload():
    """测试文件夹上传能力"""
    print("=== 文件夹上传能力验证 ===")
    
    # 扫描 dataset 目录
    r = httpx.get('http://localhost:8000/api/assets/scan')
    data = r.json()
    
    print(f"扫描状态码: {r.status_code}")
    print(f"发现资产总数: {data['total_assets']}")
    
    # 统计目录型资产
    assets = data['assets']
    dir_assets = [a for a in assets if a.get('path_type') == 'directory']
    print(f"目录型资产数: {len(dir_assets)}")
    
    for asset in dir_assets:
        print(f"\n--- 目录型资产 ---")
        print(f"名称: {asset['name']}")
        print(f"路径类型: {asset['path_type']}")
        print(f"成员文件数: {len(asset.get('member_files', []))}")
        print(f"已注册: {asset.get('registered', False)}")
        if asset.get('registered_dataset_id'):
            print(f"数据集ID: {asset['registered_dataset_id']}")
    
    return len(dir_assets) > 0

def test_multi_csv_dataset():
    """测试多 CSV 逻辑数据集导入"""
    print("\n=== 多 CSV 逻辑数据集导入验证 ===")
    
    # 获取已注册的数据集列表
    r = httpx.get('http://localhost:8000/api/datasets/')
    datasets = r.json()
    
    print(f"数据集列表状态码: {r.status_code}")
    print(f"数据集数量: {len(datasets)}")
    
    # 找到多文件数据集（需要调用详情 API 获取 files）
    multi_file_datasets = []
    for ds in datasets:
        # 调用详情 API 获取完整信息
        detail_r = httpx.get(f'http://localhost:8000/api/datasets/{ds["id"]}')
        if detail_r.status_code == 200:
            detail = detail_r.json()
            files = detail.get('files', [])
            print(f"\n--- 数据集详情 ---")
            print(f"名称: {detail['name']}")
            print(f"ID: {detail['id']}")
            print(f"文件数: {len(files)}")
            for f in files:
                print(f"  - {f['file_name']} ({f.get('role', 'unknown')})")
            
            if len(files) > 1:
                multi_file_datasets.append(detail)
    
    return len(multi_file_datasets) > 0

if __name__ == "__main__":
    folder_ok = test_folder_upload()
    multi_csv_ok = test_multi_csv_dataset()
    
    print("\n=== 验证结果 ===")
    print(f"文件夹上传能力: {'✅ 通过' if folder_ok else '❌ 失败'}")
    print(f"多 CSV 逻辑数据集导入: {'✅ 通过' if multi_csv_ok else '❌ 失败'}")
