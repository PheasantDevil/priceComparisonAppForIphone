import json
import logging
import os
from datetime import datetime

import requests

# ロギングの設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# LINE Notifyのトークン
LINE_NOTIFY_TOKEN = os.environ.get('LINE_NOTIFY_TOKEN')

def send_line_notification(message):
    """
    LINE Notifyを使用して通知を送信する
    """
    headers = {
        'Authorization': f'Bearer {LINE_NOTIFY_TOKEN}'
    }
    
    data = {
        'message': message
    }
    
    try:
        response = requests.post(
            'https://notify-api.line.me/api/notify',
            headers=headers,
            data=data
        )
        response.raise_for_status()
        logger.info('LINE通知の送信に成功しました')
        return True
    except Exception as e:
        logger.error(f'LINE通知の送信に失敗しました: {str(e)}')
        return False

def lambda_handler(event, context):
    """
    Lambda関数のメインハンドラー
    """
    try:
        # イベントからメッセージを取得
        if isinstance(event, str):
            message = event
        elif isinstance(event, dict):
            message = event.get('message', str(event))
        else:
            message = str(event)
        
        # タイムスタンプを追加
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        formatted_message = f'\n[{timestamp}]\n{message}'
        
        # LINE通知を送信
        success = send_line_notification(formatted_message)
        
        if success:
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': '通知が正常に送信されました',
                    'timestamp': timestamp
                })
            }
        else:
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'message': '通知の送信に失敗しました',
                    'timestamp': timestamp
                })
            }
            
    except Exception as e:
        logger.error(f'エラーが発生しました: {str(e)}')
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': f'エラーが発生しました: {str(e)}',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        } 