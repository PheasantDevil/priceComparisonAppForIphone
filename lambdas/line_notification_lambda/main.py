import json
import logging
import os

from linebot import LineBotApi
from linebot.models import TextSendMessage

# ログ設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# LINE Bot APIの初期化
line_bot_api = LineBotApi(os.environ['LINE_CHANNEL_ACCESS_TOKEN'])

def lambda_handler(event, context):
    try:
        # イベントから通知内容を取得
        message = event.get('message', '')
        if not message:
            raise ValueError('メッセージが指定されていません')

        # LINEにメッセージを送信
        line_bot_api.broadcast(TextSendMessage(text=message))
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': '通知を送信しました'
            })
        }
        
    except Exception as e:
        logger.error(f'エラーが発生しました: {str(e)}')
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        } 