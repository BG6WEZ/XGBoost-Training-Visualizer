"""M1 证据补齐脚本 - 修复版"""
import httpx
import json

def test_folder_upload():
    """测试文件夹上传能力"""
    print("=== 文件夹上传能力验证 ===")
    
    r = httpx.get('http://localhost:8000/api/assets/scan')
    data = r.json()
    
    print(f"扫描状态码: {r.status_code}")
    print(f"发现资产总数: {data['total_assets']}")
    
    assets = data['assets']
    dir_assets = [a for a in assets if a.get('path_type') == 'directory']
    print(f"目录型资产数: {len(dir_assets)}")
    
    for asset in dir_assets:
        print(f"\n--- 目录型资产 ---")
        print(f"名称: {asset['name']}")
        print(f"路径类型: {asset['path_type']}")
        member_count = len(asset.get('member_files', []))
        print(f"成员文件数: {member_count}")
        print(f"已注册: {asset.get('registered', False)}")
        if asset.get('registered_dataset_id'):
            print(f"数据集ID: {asset['registered_dataset_id']}")
    
    return len(dir_assets) > 0

def test_multi_csv_dataset():
    """测试多 CSV 逻辑数据集导入"""
    print("\n=== 多 CSV 逻辑数据集导入验证 ===")
    
    r = httpx.get('http://localhost:8000/api/datasets/')
    datasets = r.json()
    
    print(f"数据集列表状态码: {r.status_code}")
    print(f"数据集数量: {len(datasets)}")
    
    multi_file_datasets = []
    for ds in datasets:
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

def register_multi_file_dataset():
    """注册多文件数据集"""
    print("\n=== 注册多文件数据集 ===")
    
    r = httpx.get('http://localhost:8000/api/assets/scan')
    data = r.json()
    
    bdg2_assets = [a for a in data['assets'] if 'BDG2' in a['name'] and a.get('path_type') == 'directory']
    
    if not bdg2_assets:
        print("未找到 BDG2 目录型资产")
        return None
    
    asset = bdg2_assets[0]
    print(f"选择资产: {asset['name']}")
    print(f"成员文件数: {len(asset.get('member_files', []))}")
    
    # 构建完整的注册请求
    reg_payload = {
        "asset_name": asset['name'],
        "source_type": asset.get('source_type', 'bdg2'),
        "path": asset['path'],
        "path_type": asset['path_type'],
        "is_raw": asset.get('is_raw', False),
        "description": asset.get('description', ''),
        "member_files": asset.get('member_files', []),
        "auto_detect_columns": True
    }
    
    reg_r = httpx.post(
        'http://localhost:8000/api/assets/register',
        json=reg_payload
    )
    
    print(f"注册状态码: {reg_r.status_code}")
    
    if reg_r.status_code == 200:
        result = reg_r.json()
        print(f"注册成功! 数据集ID: {result.get('id')}")
        return result
    else:
        print(f"注册失败: {reg_r.text}")
        return None

if __name__ == "__main__":
    folder_ok = test_folder_upload()
    multi_csv_ok = test_multi_csv_dataset()
    
    if not multi_csv_ok:
        print("\n尝试注册多文件数据集...")
        result = register_multi_file_dataset()
        if result:
            multi_csv_ok = True
    
    print("\n=== 验证结果 ===")
    print(f"文件夹上传能力: {'✅ 通过' if folder_ok else '❌ 失败'}")
    print(f"多 CSV 逻辑数据集导入: {'✅ 通过' if multi_csv_ok else '❌ 失败'}")
