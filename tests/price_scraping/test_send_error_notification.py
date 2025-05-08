#!/usr/bin/env python3
"""
LINE通知機能のテスト
"""

import os
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from scripts.price_scraping.send_error_notification import (
    create_error_message, main, send_notification)


def test_create_error_message():
    """エラーメッセージ作成のテスト"""
    # スクレイピングエラー
    scraping_msg = create_error_message('scraping', 'テストエラー')
    assert 'スクレイピングエラー' in scraping_msg
    assert 'テストエラー' in scraping_msg
    
    # DynamoDBエラー
    dynamodb_msg = create_error_message('dynamodb', 'テストエラー')
    assert 'DynamoDB操作エラー' in dynamodb_msg
    assert 'テストエラー' in dynamodb_msg
    
    # 予期せぬエラー
    unexpected_msg = create_error_message('unexpected', 'テストエラー')
    assert '予期せぬエラー' in unexpected_msg
    assert 'テストエラー' in unexpected_msg
    
    # タイムスタンプの確認
    current_time = datetime.now().strftime('%Y-%m-%d')
    assert current_time in scraping_msg
    assert current_time in dynamodb_msg
    assert current_time in unexpected_msg

@patch('linebot.LineBotApi')
def test_send_notification(mock_line_bot_api):
    """通知送信のテスト"""
    # 環境変数の設定
    os.environ['LINE_CHANNEL_ACCESS_TOKEN'] = 'test_token'
    
    # テストメッセージ
    test_message = 'テスト通知メッセージ'
    
    # 通知の送信
    send_notification(test_message)
    
    # LINE Bot APIの呼び出しを確認
    mock_line_bot_api.assert_called_once_with('test_token')
    mock_line_bot_api.return_value.broadcast.assert_called_once()

@patch('linebot.LineBotApi')
def test_send_notification_error(mock_line_bot_api):
    """通知送信エラーのテスト"""
    # 環境変数の設定
    os.environ['LINE_CHANNEL_ACCESS_TOKEN'] = 'test_token'
    
    # エラーを発生させる
    mock_line_bot_api.return_value.broadcast.side_effect = Exception('テストエラー')
    
    # エラーが発生することを確認
    with pytest.raises(Exception) as exc_info:
        send_notification('テストメッセージ')
    assert 'テストエラー' in str(exc_info.value)

@patch('scripts.price_scraping.send_error_notification.send_notification')
def test_main_success(mock_send_notification):
    """メイン処理の成功テスト"""
    # コマンドライン引数のモック
    with patch('sys.argv', ['script.py', 'scraping', 'テストエラー']):
        main()
        mock_send_notification.assert_called_once()

@patch('scripts.price_scraping.send_error_notification.send_notification')
def test_main_invalid_args(mock_send_notification):
    """メイン処理の引数エラーテスト"""
    # 不正な引数で実行
    with patch('sys.argv', ['script.py']):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1
        mock_send_notification.assert_not_called()

@patch('scripts.price_scraping.send_error_notification.send_notification')
def test_main_notification_error(mock_send_notification):
    """メイン処理の通知エラーテスト"""
    # 通知送信でエラーを発生
    mock_send_notification.side_effect = Exception('テストエラー')
    
    # エラーが発生することを確認
    with patch('sys.argv', ['script.py', 'scraping', 'テストエラー']):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1 