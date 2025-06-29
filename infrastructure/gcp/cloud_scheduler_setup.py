#!/usr/bin/env python3
"""
Cloud Schedulerで価格履歴保存バッチを自動化するセットアップスクリプト
- 毎日午前9時に価格履歴を保存
- 古いデータを自動削除
"""

import json
import os
import subprocess
from datetime import datetime


def setup_cloud_scheduler():
    """Cloud Schedulerで価格履歴保存バッチをセットアップ"""
    
    # プロジェクトID
    project_id = "price-comparison-app-463007"
    
    # スケジュール設定（毎日午前9時）
    schedule = "0 9 * * *"
    
    # 実行するコマンド
    command = "python scripts/price_history_manager.py"
    
    # Cloud Schedulerジョブを作成
    job_name = "price-history-backup"
    job_description = "毎日午前9時に価格履歴を保存し、古いデータを削除"
    
    print(f"Cloud Schedulerジョブ '{job_name}' を作成中...")
    
    try:
        # Cloud Schedulerジョブを作成
        create_job_cmd = [
            "gcloud", "scheduler", "jobs", "create", "http", job_name,
            "--schedule", schedule,
            "--uri", f"https://us-central1-{project_id}.cloudfunctions.net/trigger_price_history_backup",
            "--http-method", "POST",
            "--description", job_description,
            "--project", project_id,
            "--location", "us-central1"
        ]
        
        result = subprocess.run(create_job_cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Cloud Schedulerジョブ '{job_name}' が正常に作成されました")
            print(f"   スケジュール: {schedule}")
            print(f"   説明: {job_description}")
        else:
            print(f"❌ Cloud Schedulerジョブの作成に失敗しました")
            print(f"   エラー: {result.stderr}")
            
            # 既存のジョブを更新
            print("既存のジョブを更新します...")
            update_job_cmd = [
                "gcloud", "scheduler", "jobs", "update", "http", job_name,
                "--schedule", schedule,
                "--uri", f"https://us-central1-{project_id}.cloudfunctions.net/trigger_price_history_backup",
                "--http-method", "POST",
                "--description", job_description,
                "--project", project_id,
                "--location", "us-central1"
            ]
            
            update_result = subprocess.run(update_job_cmd, capture_output=True, text=True)
            if update_result.returncode == 0:
                print(f"✅ Cloud Schedulerジョブ '{job_name}' が正常に更新されました")
            else:
                print(f"❌ Cloud Schedulerジョブの更新に失敗しました")
                print(f"   エラー: {update_result.stderr}")
    
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")

def create_trigger_function():
    """価格履歴保存をトリガーするCloud Functionを作成"""
    
    print("価格履歴保存トリガー用のCloud Functionを作成中...")
    
    # トリガー関数のコード
    trigger_code = '''
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
'''
    
    # トリガー関数用のディレクトリを作成
    trigger_dir = "functions/trigger_price_history_backup"
    os.makedirs(trigger_dir, exist_ok=True)
    
    # main.pyを作成
    with open(f"{trigger_dir}/main.py", "w", encoding="utf-8") as f:
        f.write(trigger_code)
    
    # requirements.txtを作成
    with open(f"{trigger_dir}/requirements.txt", "w", encoding="utf-8") as f:
        f.write("functions-framework==3.*\n")
        f.write("google-cloud-firestore\n")
        f.write("google-oauth2\n")
    
    print(f"✅ トリガー関数のコードを作成しました: {trigger_dir}")
    
    # Cloud Functionをデプロイ
    try:
        deploy_cmd = [
            "gcloud", "functions", "deploy", "trigger_price_history_backup",
            "--runtime", "python310",
            "--trigger-http",
            "--allow-unauthenticated",
            "--entry-point", "trigger_price_history_backup",
            "--source", trigger_dir
        ]
        
        result = subprocess.run(deploy_cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ トリガー関数が正常にデプロイされました")
        else:
            print(f"❌ トリガー関数のデプロイに失敗しました: {result.stderr}")
    
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")

def main():
    """メイン処理"""
    print("=== Cloud Scheduler セットアップ ===")
    print()
    
    # 1. トリガー関数を作成・デプロイ
    create_trigger_function()
    print()
    
    # 2. Cloud Schedulerジョブをセットアップ
    setup_cloud_scheduler()
    print()
    
    print("=== セットアップ完了 ===")
    print("毎日午前9時に価格履歴保存バッチが自動実行されます")

if __name__ == "__main__":
    main() 