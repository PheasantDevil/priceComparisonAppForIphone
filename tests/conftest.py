import os
import shutil
import sys
from pathlib import Path

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

@pytest.fixture(scope="function")
def test_config_file(tmp_path):
    """テスト用の設定ファイルを作成するフィクスチャ"""
    config_content = """
scraper:
  selectors:
    price_item: ".price-item"
    model: ".model"
    price: ".price"
    condition: ".condition"
  user_agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
  max_retries: 3
  timeout: 30
  cache_duration: 3600

urls:
  kaitori:
    - "https://example.com/kaitori"
    - "https://example.com/kaitori2"
  official:
    - "https://example.com/official"
    - "https://example.com/official2"

dynamodb:
  table_name: "price_comparison_test"
  region: "ap-northeast-1"
  read_capacity: 5
  write_capacity: 5
"""
    # 設定ファイルの保存先ディレクトリを作成
    config_dir = Path(__file__).parent.parent / "src" / "lambda_functions" / "get_prices_lambda" / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # 設定ファイルを作成
    config_file = config_dir / "config.test.yaml"
    config_file.write_text(config_content)
    
    yield config_file
    
    # テスト後にファイルを削除
    if config_file.exists():
        config_file.unlink()

@pytest.fixture(autouse=True)
def setup_test_env():
    """テスト環境のセットアップ"""
    # テスト用の環境変数を設定
    os.environ['DYNAMODB_TABLE'] = 'test_prices'
    os.environ['ERROR_NOTIFICATION_TOPIC_ARN'] = 'arn:aws:sns:ap-northeast-1:123456789012:test-topic'
    
    yield
    
    # テスト後のクリーンアップ
    if 'DYNAMODB_TABLE' in os.environ:
        del os.environ['DYNAMODB_TABLE']
    if 'ERROR_NOTIFICATION_TOPIC_ARN' in os.environ:
        del os.environ['ERROR_NOTIFICATION_TOPIC_ARN']
