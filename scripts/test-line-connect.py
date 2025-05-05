import json
import logging
import os

from linebot import LineBotApi
from linebot.exceptions import LineBotApiError
from linebot.models import TextSendMessage

# ログ設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    try:
        # LINE Bot APIの初期化
        line_bot_api = LineBotApi(os.environ['LINE_CHANNEL_ACCESS_TOKEN'])
        
        # テストメッセージの送信
        message = TextSendMessage(text='テスト通知: iPhone価格アラートシステムが正常に動作しています。')
        line_bot_api.broadcast(message)
        
        return {
            'statusCode': 200,
            'body': json.dumps('通知が正常に送信されました')
        }
    except LineBotApiError as e:
        logger.error(f"LINE APIエラー: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'通知の送信に失敗しました: {str(e)}')
        }
    except Exception as e:
        logger.error(f"予期せぬエラー: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'予期せぬエラーが発生しました: {str(e)}')
        }