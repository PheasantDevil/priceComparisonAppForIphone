import os
import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

# プロジェクトのルートディレクトリをPythonパスに追加
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

# 環境変数の設定
os.environ["PYTHONPATH"] = project_root
os.environ["FLASK_ENV"] = "testing"
os.environ["SECRET_KEY"] = "test-secret-key-16ch"
os.environ["LOG_LEVEL"] = "DEBUG"

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
        "SECRET_KEY": "test-secret-key-16ch",
        "LOG_LEVEL": "DEBUG"
    }
    for key, value in test_vars.items():
        monkeypatch.setenv(key, value)
    return test_vars

@pytest.fixture
def mock_config():
    """Mock configuration for the scraper."""
    return {
        'scraper': {
            'selectors': {
                'price_item': '.price-item',
                'model': '.model',
                'price': '.price',
                'condition': '.condition'
            },
            'headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            },
            'max_retries': 3,
            'timeout': 30,
            'cache_duration': 3600
        }
    }

@pytest.fixture
def mock_cache_dir(tmp_path):
    """Create a temporary cache directory."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    return cache_dir

@pytest.fixture
def mock_response():
    """Mock HTTP response with HTML content."""
    response = type('Response', (), {})()
    response.text = """
    <div class="price-item">
        <div class="model">iPhone 15 Pro 256GB</div>
        <div class="price">150000</div>
        <div class="condition">新品</div>
    </div>
    <div class="price-item">
        <div class="model">iPhone 15 Pro Max 512GB</div>
        <div class="price">180000</div>
        <div class="condition">中古</div>
    </div>
    """
    return response

@pytest.fixture
def test_config_file(tmp_path):
    """Create a temporary YAML configuration file."""
    config_content = """
app:
  debug: true
  log_level: DEBUG
  secret_key: test-secret-key-16ch

scraper:
  kaitori_rudea_urls:
    - "https://kaitori-rudeya.com/category/detail/183"  # iPhone 16
    - "https://kaitori-rudeya.com/category/detail/185"  # iPhone 16 Pro
    - "https://kaitori-rudeya.com/category/detail/186"  # iPhone 16 Pro Max
    - "https://kaitori-rudeya.com/category/detail/205"  # iPhone 16 e
  apple_store_url: "https://www.apple.com/jp/shop/buy-iphone"
  request_timeout: 30
  retry_count: 3
  user_agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
"""
    config_file = tmp_path / "config.testing.yaml"
    config_file.write_text(config_content)
    
    # ConfigManagerが参照するディレクトリにファイルをコピー
    dest_dir = Path(__file__).parent.parent / "config"
    dest_dir.mkdir(exist_ok=True)
    dest_file = dest_dir / "config.testing.yaml"
    shutil.copy(str(config_file), str(dest_file))
    
    yield dest_file
    
    # テスト後にファイルを削除
    if dest_file.exists():
        dest_file.unlink()

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
        yaml.dump(test_config, f)
    
    yield
    
    # Cleanup
    if (config_dir / "config.test.yaml").exists():
        (config_dir / "config.test.yaml").unlink()
