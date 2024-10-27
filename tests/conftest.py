import pytest
from pathlib import Path
import shutil

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
app:
  debug: true
  log_level: DEBUG
  secret_key: test-secret-key-16

scraper:
  kaitori_rudea_urls:
    - https://test1.example.com/kaitori
    - https://test2.example.com/kaitori
  apple_store_url: https://test.example.com/apple
  request_timeout: 30
  retry_count: 3
  user_agent: "Test User Agent"
"""
    config_file = tmp_path / "config.testing.yaml"
    config_file.write_text(config_content)
    
    # ConfigManagerが参照するディレクトリにファイルをコピー
    dest_dir = Path(__file__).parent.parent / "config"
    dest_file = dest_dir / "config.testing.yaml"
    dest_dir.mkdir(exist_ok=True)
    shutil.copy(str(config_file), str(dest_file))
    
    yield dest_file
    
    # テスト後にファイルを削除
    dest_file.unlink()
