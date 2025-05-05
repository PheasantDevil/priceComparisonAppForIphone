import base64
import json
import logging
import os
import re
import sys

from linebot.v3.messaging import (ApiClient, Configuration, MessagingApi,
                                  TextMessage)
from linebot.v3.messaging.exceptions import ApiException

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def validate_token(token):
    """チャネルアクセストークンの形式を検証"""
    if not token:
        return False
    
    # Base64エンコードされたトークンのパターン
    base64_pattern = r'^[A-Za-z0-9+/=]+$'
    
    # トークンがBase64エンコードされているか確認
    if re.match(base64_pattern, token):
        try:
            # Base64デコードを試みる
            decoded = base64.b64decode(token)
            # デコードされたトークンが適切な長さか確認
            return len(decoded) >= 32
        except:
            return False
    
    # 通常のトークンの形式（43文字の英数字）
    return len(token) == 43 and token.isalnum()

def test_line_notification():
    try:
        # 環境変数からアクセストークンを取得
        channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
        
        if not channel_access_token:
            logger.error("LINE_CHANNEL_ACCESS_TOKEN 環境変数が設定されていません")
            logger.info("以下のコマンドで環境変数を設定してください：")
            logger.info("export LINE_CHANNEL_ACCESS_TOKEN='your_channel_access_token'")
            return False
            
        if not validate_token(channel_access_token):
            logger.error("無効なチャネルアクセストークン形式です")
            logger.info("LINE Developers コンソールから正しいアクセストークンを取得してください")
            logger.info("現在のトークン: %s", channel_access_token)
            return False

        logger.info("チャネルアクセストークンの検証に成功しました")
        
        # LINE Bot APIの初期化（v3）
        configuration = Configuration(
            access_token=channel_access_token
        )
        
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            
            # テストメッセージの送信
            message = TextMessage(text='テスト通知: iPhone価格アラートシステムが正常に動作しています。')
            line_bot_api.broadcast(
                broadcast_request={
                    'messages': [message]
                }
            )
            
            logger.info("通知が正常に送信されました")
            return True
    except ApiException as e:
        logger.error(f"LINE APIエラー: {str(e)}")
        logger.error(f"エラー詳細: {e.body}")
        logger.error("以下の点を確認してください：")
        logger.error("1. チャネルアクセストークンが正しいか")
        logger.error("2. トークンが有効期限内か")
        logger.error("3. トークンに必要な権限があるか")
        return False
    except Exception as e:
        logger.error(f"予期せぬエラー: {str(e)}")
        return False

if __name__ == "__main__":
    # 環境変数の設定（テスト用）
    # 実際のチャネルアクセストークンを設定してください
    if not os.getenv('LINE_CHANNEL_ACCESS_TOKEN'):
        logger.error("LINE_CHANNEL_ACCESS_TOKEN 環境変数が設定されていません")
        logger.info("以下のコマンドで環境変数を設定してください：")
        logger.info("export LINE_CHANNEL_ACCESS_TOKEN='your_channel_access_token'")
        sys.exit(1)
    
    # テスト実行
    success = test_line_notification()
    if success:
        print("✅ テストが正常に完了しました")
    else:
        print("❌ テストが失敗しました") 