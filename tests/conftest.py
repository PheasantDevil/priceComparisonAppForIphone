import os
import shutil
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# プロジェクトのルートディレクトリをPythonパスに追加
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

# 環境変数の設定
os.environ["PYTHONPATH"] = project_root

# テスト用の設定
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )

@pytest.fixture(scope="function")
def mock_env_vars(monkeypatch):
    """環境変数をモックするフィクスチャ"""
    test_vars = {
        "FLASK_ENV": "testing",
        "SECRET_KEY": "test-secret-key-16ch",  # 16文字以上に変更
        "LOG_LEVEL": "DEBUG"
    }
    for key, value in test_vars.items():
        monkeypatch.setenv(key, value)
    return test_vars

@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    return {
        'scraper': {
            'selectors': {
                'price_item': '.price-item',
                'model': '.model',
                'price': '.price',
                'condition': '.condition'
            },
            'headers': {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            },
            'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'max_retries': 3,
            'timeout': 30,
            'cache_duration': 3600
        },
        'urls': {
            'kaitori': ['https://example.com/kaitori'],
            'official': ['https://example.com/official']
        }
    }

@pytest.fixture
def mock_response():
    """Mock HTTP response for testing."""
    mock = MagicMock()
    mock.text = """
    <div class="price-item">
        <div class="model">iPhone 15 Pro 256GB</div>
        <div class="price">150,000</div>
        <div class="condition">新品</div>
    </div>
    """
    mock.raise_for_status = MagicMock()
    return mock

@pytest.fixture
def mock_cache_dir(tmp_path):
    """Create a temporary cache directory for testing."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    return cache_dir

@pytest.fixture(autouse=True)
def setup_test_env():
    """Set up test environment."""
    # Create test configuration file
    config_dir = Path("src/lambda_functions/get_prices_lambda/config")
    config_dir.mkdir(parents=True, exist_ok=True)
    
    test_config = {
        'scraper': {
            'selectors': {
                'price_item': '.price-item',
                'model': '.model',
                'price': '.price',
                'condition': '.condition'
            },
            'headers': {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            },
            'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'max_retries': 3,
            'timeout': 30,
            'cache_duration': 3600
        },
        'urls': {
            'kaitori': ['https://example.com/kaitori'],
            'official': ['https://example.com/official']
        }
    }
    
    with open(config_dir / "config.test.yaml", 'w') as f:
        import yaml
        yaml.dump(test_config, f)
    
    yield
    
    # Cleanup
    if (config_dir / "config.test.yaml").exists():
        (config_dir / "config.test.yaml").unlink()
