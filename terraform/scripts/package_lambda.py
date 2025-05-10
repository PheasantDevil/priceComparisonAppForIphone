#!/usr/bin/env python3

"""
使用方法:
このスクリプトは、Lambda関数のパッケージングとデプロイに使用されます。
以下のコマンドで実行します：
    python3 package_lambda.py

必要な環境変数:
- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY
- AWS_DEFAULT_REGION

パッケージングされるLambda関数:
- deployment-verification: デプロイメント検証用
- smoke-test: スモークテスト用

各Lambda関数は以下の手順でパッケージングされます：
1. 依存関係のインストール
2. ZIPファイルの作成
3. Lambda関数のデプロイ
"""

import logging
import os
import shutil
import subprocess
import sys
import zipfile

import boto3

# ロギングの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def install_dependencies(requirements_file, target_dir):
    """依存関係をインストール"""
    try:
        logger.info(f"Installing dependencies from {requirements_file}...")
        subprocess.run([
            sys.executable, "-m", "pip", "install",
            "-r", requirements_file,
            "--target", target_dir
        ], check=True)
        logger.info("Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dependencies: {e}")
        raise
    except Exception as e:
        logger.error(f"Error installing dependencies: {e}")
        raise

def create_zip_file(source_dir, output_file):
    """ZIPファイルを作成"""
    try:
        logger.info(f"Creating ZIP file {output_file}...")
        with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(source_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, source_dir)
                    zipf.write(file_path, arcname)
        logger.info(f"ZIP file created successfully: {output_file}")
        return output_file
    except Exception as e:
        logger.error(f"Error creating ZIP file: {e}")
        raise

def deploy_lambda_function(function_name, zip_file):
    """Lambda関数をデプロイ"""
    try:
        logger.info(f"Deploying Lambda function {function_name}...")
        lambda_client = boto3.client('lambda')
        
        with open(zip_file, 'rb') as f:
            zip_content = f.read()
        
        response = lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_content
        )
        
        logger.info(f"Successfully deployed Lambda function {function_name}")
        return response
    except Exception as e:
        logger.error(f"Error deploying Lambda function {function_name}: {e}")
        raise

def package_and_deploy_lambda(script_name, requirements_file):
    """Lambda関数をパッケージ化してデプロイ"""
    # スクリプトのディレクトリを取得
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 一時ディレクトリの作成
    temp_dir = os.path.join(script_dir, f"temp_{script_name}")
    os.makedirs(temp_dir, exist_ok=True)

    try:
        # スクリプトをコピー
        script_path = os.path.join(script_dir, f"{script_name}.py")
        if not os.path.exists(script_path):
            raise FileNotFoundError(f"Script file not found: {script_path}")
        
        shutil.copy2(script_path, os.path.join(temp_dir, f"{script_name}.py"))
        logger.info(f"Copied script file: {script_path}")

        # 依存関係をインストール
        install_dependencies(requirements_file, temp_dir)

        # ZIPファイルを作成
        output_file = os.path.join(script_dir, f"{script_name}.zip")
        zip_path = create_zip_file(temp_dir, output_file)

        if not os.path.exists(zip_path):
            raise FileNotFoundError(f"ZIP file not created: {zip_path}")

        # Lambda関数をデプロイ
        deploy_lambda_function(script_name, zip_path)

        logger.info(f"Successfully packaged and deployed {script_name}.py")
        return zip_path

    except Exception as e:
        logger.error(f"Error packaging and deploying Lambda function {script_name}: {e}")
        raise
    finally:
        # 一時ディレクトリを削除
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            logger.info(f"Cleaned up temporary directory: {temp_dir}")

def main():
    """メイン関数"""
    try:
        # スクリプトのディレクトリを取得
        script_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(os.path.dirname(script_dir))
        
        # requirements-base.txtのパスを設定
        requirements_path = os.path.join(root_dir, "requirements-base.txt")
        if not os.path.exists(requirements_path):
            raise FileNotFoundError(f"Requirements file not found: {requirements_path}")
        
        # デプロイメント検証用のLambda関数をパッケージ化してデプロイ
        package_and_deploy_lambda("deployment-verification", requirements_path)
        
        # スモークテスト用のLambda関数をパッケージ化してデプロイ
        package_and_deploy_lambda("smoke-test", requirements_path)
        
        logger.info("All Lambda functions packaged and deployed successfully")

    except Exception as e:
        logger.error(f"Error in main function: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 