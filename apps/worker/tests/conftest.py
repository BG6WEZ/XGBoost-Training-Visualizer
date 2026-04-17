"""Shared test fixtures for Worker tests."""
import os
import tempfile
import uuid
import pandas as pd
import numpy as np
import pytest
import pytest_asyncio
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_csv_file(temp_dir):
    """Create a sample CSV file for training/preprocessing tests."""
    csv_path = os.path.join(temp_dir, "sample_data.csv")
    np.random.seed(42)
    n_rows = 200
    df = pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=n_rows, freq='h'),
        'feature_a': np.random.randn(n_rows) * 10 + 50,
        'feature_b': np.random.randn(n_rows) * 5 + 20,
        'feature_c': np.random.choice(['X', 'Y', 'Z'], n_rows),
        'target': np.random.randn(n_rows) * 20 + 100,
    })
    df.to_csv(csv_path, index=False)
    return csv_path


@pytest.fixture
def sample_csv_invalid_target(temp_dir):
    """Create a CSV file with invalid target values for error testing."""
    csv_path = os.path.join(temp_dir, "invalid_data.csv")
    df = pd.DataFrame({
        'feature_a': [1, 2, 3, 4, 5],
        'target': ['invalid', 'not_a_number', None, float('inf'), float('nan')],
    })
    df.to_csv(csv_path, index=False)
    return csv_path


@pytest.fixture
def sample_csv_missing_target(temp_dir):
    """Create a CSV file where target column doesn't exist."""
    csv_path = os.path.join(temp_dir, "missing_target.csv")
    df = pd.DataFrame({
        'feature_a': [1, 2, 3],
        'feature_b': [4, 5, 6],
    })
    df.to_csv(csv_path, index=False)
    return csv_path


@pytest.fixture
def mock_storage():
    """Mock storage service that doesn't depend on real filesystem."""
    mock = MagicMock()
    mock.save_preprocessing_output = AsyncMock(return_value={
        "storage_type": "mock",
        "object_key": "mock/preprocessing_output.csv",
        "file_size": 1024,
    })
    mock.save_feature_engineering_output = AsyncMock(return_value={
        "storage_type": "mock",
        "object_key": "mock/feature_output.csv",
        "file_size": 2048,
    })
    mock.save_prediction_data = AsyncMock()
    return mock


@pytest.fixture
def mock_redis():
    """Mock Redis connection."""
    mock = MagicMock()
    mock.ping = MagicMock(return_value=True)
    mock.get = MagicMock(return_value=None)
    mock.set = MagicMock()
    mock.delete = MagicMock()
    mock.blpop = MagicMock(return_value=None)
    mock.lpush = MagicMock()
    return mock