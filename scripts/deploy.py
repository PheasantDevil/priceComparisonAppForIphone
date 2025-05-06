#!/usr/bin/env python3

"""
使用方法:
このスクリプトは、AWSリソースのデプロイメントを実行します。
以下のコマンドで実行します：
    python3 deploy.py

必要な環境変数:
- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY
- AWS_DEFAULT_REGION

デプロイメント手順:
1. Lambda関数のパッケージング
2. Terraformの実行
3. デプロイメントの検証
"""

import json
import logging
import os
import subprocess
import sys
import time

# ロギングの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_command(command, cwd=None):
    """コマンドを実行し、結果を返す"""
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, f"Error executing command: {e.stderr}"

def package_lambda_functions():
    """Lambda関数をパッケージング"""
    logger.info("Packaging Lambda functions...")
    success, output = run_command(["python3", "package_lambda.py"], cwd="scripts")
    if not success:
        logger.error(f"Failed to package Lambda functions: {output}")
        return False
    logger.info("Lambda functions packaged successfully")
    return True

def run_terraform():
    """Terraformを実行"""
    logger.info("Running Terraform...")
    
    # Terraformの初期化
    success, output = run_command(["terraform", "init"], cwd="terraform")
    if not success:
        logger.error(f"Failed to initialize Terraform: {output}")
        return False
    logger.info("Terraform initialized successfully")

    # Terraformの実行
    success, output = run_command(["terraform", "apply", "-auto-approve"], cwd="terraform")
    if not success:
        logger.error(f"Failed to apply Terraform: {output}")
        return False
    logger.info("Terraform applied successfully")
    return True

def verify_deployment():
    """デプロイメントを検証"""
    logger.info("Verifying deployment...")
    success, output = run_command(["python3", "deployment-verification.py"], cwd="scripts")
    if not success:
        logger.error(f"Deployment verification failed: {output}")
        return False

    try:
        result = json.loads(output)
        if result['status'] == 'success':
            logger.info("Deployment verification successful")
            return True
        else:
            logger.error(f"Deployment verification failed: {result['message']}")
            return False
    except json.JSONDecodeError:
        logger.error("Failed to parse verification output")
        return False

def main():
    """メイン関数"""
    try:
        # 必要な環境変数の確認
        required_env_vars = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_DEFAULT_REGION']
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        if missing_vars:
            logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
            return 1

        # デプロイメント手順の実行
        steps = [
            ("Packaging Lambda functions", package_lambda_functions),
            ("Running Terraform", run_terraform),
            ("Verifying deployment", verify_deployment)
        ]

        for step_name, step_func in steps:
            logger.info(f"Starting: {step_name}")
            if not step_func():
                logger.error(f"Failed: {step_name}")
                return 1
            logger.info(f"Completed: {step_name}")

        logger.info("Deployment completed successfully")
        return 0

    except Exception as e:
        logger.error(f"Unexpected error during deployment: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 