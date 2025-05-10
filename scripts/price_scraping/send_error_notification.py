#!/usr/bin/env python3
"""
エラー通知スクリプト
- スクレイピングエラー
- DynamoDB操作エラー
- その他の予期せぬエラー
の通知をLINEで送信
"""

import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, Optional

import yaml
from linebot import LineBotApi
from linebot.exceptions import LineBotApiError
from linebot.models import TextSendMessage

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_error_message(error_type: str, error_message: str) -> str:
    """エラーメッセージの作成"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    request_id = os.environ.get('AWS_REQUEST_ID', 'unknown')
    
    # エラータイプに応じたメッセージを生成
    if error_type == 'scraping':
        title = "スクレイピングエラー"
    elif error_type == 'dynamodb':
        title = "DynamoDB操作エラー"
    else:
        title = "予期せぬエラー"
    
    return f"""
🚨 {title} 🚨
時刻: {timestamp}
Request ID: {request_id}

エラー内容:
{error_message}

システムは自動的に再試行を行います。
"""

def send_notification(message: str) -> None:
    """LINE通知の送信"""
    try:
        # 環境変数からLINEチャネルアクセストークンを取得
        channel_access_token = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
        if not channel_access_token:
            logger.error("LINE_CHANNEL_ACCESS_TOKEN環境変数が設定されていません")
            raise ValueError("LINE_CHANNEL_ACCESS_TOKENが必要です")

        # LINE Bot APIの初期化
        line_bot_api = LineBotApi(channel_access_token)
        
        # メッセージの送信
        text_message = TextSendMessage(text=message)
        line_bot_api.broadcast(text_message)
        
        logger.info(f"LINE通知を送信しました (Request ID: {os.environ.get('AWS_REQUEST_ID', 'unknown')})")
        
    except LineBotApiError as e:
        logger.error(f"LINE APIエラー: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"通知送信エラー: {str(e)}")
        raise

def main():
    """メイン処理"""
    try:
        # コマンドライン引数の確認
        if len(sys.argv) != 3:
            logger.error("引数の数が不正です")
            logger.error("使用方法: python send_error_notification.py <error_type> <error_message>")
            sys.exit(1)
        
        # 引数の取得
        error_type = sys.argv[1]
        error_message = sys.argv[2]
        
        # エラーメッセージの作成
        message = create_error_message(error_type, error_message)
        
        # 通知の送信
        send_notification(message)
        
    except Exception as e:
        logger.error(f"予期せぬエラー: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 