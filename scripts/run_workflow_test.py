#!/usr/bin/env python3
"""
ワークフローテストの実行スクリプト
"""

import os
import sys
from pathlib import Path

# プロジェクトのルートディレクトリをPYTHONPATHに追加
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# テストモジュールをインポート
from scripts.price_scraping.test_workflow import main

if __name__ == "__main__":
    # 必要な環境変数の確認
    required_env_vars = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'LINE_CHANNEL_ACCESS_TOKEN']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"エラー: 以下の環境変数が設定されていません: {', '.join(missing_vars)}")
        print("以下のコマンドで環境変数を設定してください:")
        print("export AWS_ACCESS_KEY_ID='your_access_key'")
        print("export AWS_SECRET_ACCESS_KEY='your_secret_key'")
        print("export LINE_CHANNEL_ACCESS_TOKEN='your_line_token'")
        sys.exit(1)
    
    # テストの実行
    sys.exit(main()) 