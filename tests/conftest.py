import pytest
from pathlib import Path
import os



@pytest.fixture
def temp_config_dir(tmp_path):
    """一時的な設定ファイルディレクトリを作成するフィクスチャ"""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir

@pytest.fixture(scope="function")
def mock_env_vars(monkeypatch):
    """環境変数をモックするフィクスチャ"""
    monkeypatch.setenv("FLASK_ENV", "testing")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-12345")
    return {
        "FLASK_ENV": "testing",
        "SECRET_KEY": "test-secret-key-12345"
    }

@pytest.fixture
def test_config_file(temp_config_dir):
    """テスト用の設定ファイルを作成するフィクスチャ"""
    config_content = """
app:
  debug: true
  log_level: DEBUG
  secret_key: test-secret-key

scraper:
  kaitori_rudea_url: https://test.example.com/kaitori
  apple_store_url: https://test.example.com/apple
  request_timeout: 30
  retry_count: 3
  user_agent: "Test User Agent"
"""
    config_file = temp_config_dir / "config.testing.yaml"
    config_file.write_text(config_content)
    return config_file
