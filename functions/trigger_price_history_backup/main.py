
import functions_framework
import requests
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

@functions_framework.http
def trigger_price_history_backup(request):
    """価格履歴保存をトリガーするCloud Function"""
    
    # CORSヘッダー
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'POST,OPTIONS'
    }
    
    # OPTIONSリクエストの処理
    if request.method == 'OPTIONS':
        return ('', 204, headers)
    
    try:
        logger.info("価格履歴保存バッチを開始")
        
        # 価格履歴保存スクリプトを実行
        import subprocess
        import sys
        import os
        
        # スクリプトのパスを設定
        script_path = os.path.join(os.getcwd(), 'scripts', 'price_history_manager.py')
        
        # Pythonスクリプトを実行
        result = subprocess.run([
            sys.executable, script_path
        ], capture_output=True, text=True, cwd=os.getcwd())
        
        if result.returncode == 0:
            logger.info("価格履歴保存バッチが正常に完了")
            return (json.dumps({
                'status': 'success',
                'message': '価格履歴保存バッチが正常に完了しました'
            }), 200, headers)
        else:
            logger.error(f"価格履歴保存バッチが失敗: {result.stderr}")
            return (json.dumps({
                'status': 'error',
                'message': f'価格履歴保存バッチが失敗しました: {result.stderr}'
            }), 500, headers)
            
    except Exception as e:
        logger.error(f"エラーが発生しました: {str(e)}")
        return (json.dumps({
            'status': 'error',
            'message': f'エラーが発生しました: {str(e)}'
        }), 500, headers)
