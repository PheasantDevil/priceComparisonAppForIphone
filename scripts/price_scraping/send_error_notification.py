#!/usr/bin/env python3
"""
エラー通知スクリプト
- スクレイピングエラー
- DynamoDB操作エラー
- その他の予期せぬエラー
の通知を送信
"""

import json
import logging
import os
import sys
from datetime import datetime

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
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    message = f"""
🚨 エラーが発生しました 🚨

発生時刻: {current_time}
エラーの種類: {error_type}
エラー内容: {error_message}

対応が必要な場合は、ログを確認してください。
"""
    return message

def send_notification(message: str) -> None:
    """LINE通知の送信"""
    try:
        line_bot_api = LineBotApi(os.environ['LINE_CHANNEL_ACCESS_TOKEN'])
        line_bot_api.broadcast(TextSendMessage(text=message))
    except LineBotApiError as e:
        logger.error(f"LINE通知の送信に失敗: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"予期せぬエラー: {e}")
        sys.exit(1)

def main():
    if len(sys.argv) != 3:
        logger.error("引数が不正です")
        sys.exit(1)
    
    error_type = sys.argv[1]
    error_message = sys.argv[2]
    
    message = create_error_message(error_type, error_message)
    send_notification(message)

if __name__ == "__main__":
    main() 