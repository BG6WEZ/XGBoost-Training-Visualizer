"""特征工程校验测试脚本"""
from pydantic import ValidationError
from app.schemas.dataset import FeatureEngineeringRequest


def test_valid_feature_engineering_config():
    """测试有效的特征工程配置"""
    print("测试 1: 有效的特征工程配置")
    
    valid_config = {
        "dataset_id": "test-dataset-id",
        "config": {
            "time_features": {
                "enabled": True,
                "column": "timestamp",
                "features": ["hour", "dayofweek", "month", "is_weekend"]
            },
            "lag_features": {
                "enabled": True,
                "columns": ["energy_consumption"],
                "lags": [1, 6, 12, 24]
            },
            "rolling_features": {
                "enabled": True,
                "columns": ["energy_consumption"],
                "windows": [3, 6, 24]
            }
        }
    }
    
    try:
        request = FeatureEngineeringRequest(**valid_config)
        print("✓ 有效的配置通过验证")
        return True
    except ValidationError as e:
        print(f"✗ 有效的配置验证失败: {e}")
        return False


def test_invalid_time_feature():
    """测试无效的时间特征"""
    print("\n测试 2: 无效的时间特征")
    
    invalid_config = {
        "dataset_id": "test-dataset-id",
        "config": {
            "time_features": {
                "enabled": True,
                "column": "timestamp",
                "features": ["hour", "day_of_week"]  # 无效特征
            },
            "lag_features": {
                "enabled": False
            },
            "rolling_features": {
                "enabled": False
            }
        }
    }
    
    try:
        request = FeatureEngineeringRequest(**invalid_config)
        print("✗ 无效的时间特征未被检测到")
        return False
    except ValidationError as e:
        print(f"✓ 无效的时间特征被正确检测: {e}")
        return True


def test_missing_time_column():
    """测试缺少时间列"""
    print("\n测试 3: 缺少时间列")
    
    invalid_config = {
        "dataset_id": "test-dataset-id",
        "config": {
            "time_features": {
                "enabled": True,
                "features": ["hour", "dayofweek"]  # 缺少 column
            },
            "lag_features": {
                "enabled": False
            },
            "rolling_features": {
                "enabled": False
            }
        }
    }
    
    try:
        request = FeatureEngineeringRequest(**invalid_config)
        print("✗ 缺少时间列未被检测到")
        return False
    except ValidationError as e:
        print(f"✓ 缺少时间列被正确检测: {e}")
        return True


def test_invalid_lag_value():
    """测试无效的滞后值"""
    print("\n测试 4: 无效的滞后值")
    
    invalid_config = {
        "dataset_id": "test-dataset-id",
        "config": {
            "time_features": {
                "enabled": False
            },
            "lag_features": {
                "enabled": True,
                "columns": ["energy_consumption"],
                "lags": [1, 0, -1]  # 包含无效值
            },
            "rolling_features": {
                "enabled": False
            }
        }
    }
    
    try:
        request = FeatureEngineeringRequest(**invalid_config)
        print("✗ 无效的滞后值未被检测到")
        return False
    except ValidationError as e:
        print(f"✓ 无效的滞后值被正确检测: {e}")
        return True


def test_invalid_window_value():
    """测试无效的窗口值"""
    print("\n测试 5: 无效的窗口值")
    
    invalid_config = {
        "dataset_id": "test-dataset-id",
        "config": {
            "time_features": {
                "enabled": False
            },
            "lag_features": {
                "enabled": False
            },
            "rolling_features": {
                "enabled": True,
                "columns": ["energy_consumption"],
                "windows": [3, 0, -1]  # 包含无效值
            }
        }
    }
    
    try:
        request = FeatureEngineeringRequest(**invalid_config)
        print("✗ 无效的窗口值未被检测到")
        return False
    except ValidationError as e:
        print(f"✓ 无效的窗口值被正确检测: {e}")
        return True


def test_missing_lag_columns():
    """测试缺少滞后特征列"""
    print("\n测试 6: 缺少滞后特征列")
    
    invalid_config = {
        "dataset_id": "test-dataset-id",
        "config": {
            "time_features": {
                "enabled": False
            },
            "lag_features": {
                "enabled": True,
                "lags": [1, 6, 12, 24]  # 缺少 columns
            },
            "rolling_features": {
                "enabled": False
            }
        }
    }
    
    try:
        request = FeatureEngineeringRequest(**invalid_config)
        print("✗ 缺少滞后特征列未被检测到")
        return False
    except ValidationError as e:
        print(f"✓ 缺少滞后特征列被正确检测: {e}")
        return True


def test_missing_rolling_columns():
    """测试缺少滚动特征列"""
    print("\n测试 7: 缺少滚动特征列")
    
    invalid_config = {
        "dataset_id": "test-dataset-id",
        "config": {
            "time_features": {
                "enabled": False
            },
            "lag_features": {
                "enabled": False
            },
            "rolling_features": {
                "enabled": True,
                "windows": [3, 6, 24]  # 缺少 columns
            }
        }
    }
    
    try:
        request = FeatureEngineeringRequest(**invalid_config)
        print("✗ 缺少滚动特征列未被检测到")
        return False
    except ValidationError as e:
        print(f"✓ 缺少滚动特征列被正确检测: {e}")
        return True


if __name__ == "__main__":
    print("=== 特征工程校验测试 ===")
    print("=" * 50)
    
    tests = [
        test_valid_feature_engineering_config,
        test_invalid_time_feature,
        test_missing_time_column,
        test_invalid_lag_value,
        test_invalid_window_value,
        test_missing_lag_columns,
        test_missing_rolling_columns
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("✓ 所有测试通过！")
    else:
        print("✗ 部分测试失败！")
