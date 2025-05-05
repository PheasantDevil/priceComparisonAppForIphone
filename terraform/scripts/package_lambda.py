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

def package_lambda_function(lambda_dir, output_dir, output_file=None):
    """Lambda関数をパッケージ化"""
    try:
        logger.info(f"Packaging Lambda function from {lambda_dir}...")
        
        # 一時ディレクトリの作成
        temp_dir = os.path.join(output_dir, f"temp_{os.path.basename(lambda_dir)}")
        os.makedirs(temp_dir, exist_ok=True)

        try:
            # Lambda関数のコードをコピー
            for item in os.listdir(lambda_dir):
                src_path = os.path.join(lambda_dir, item)
                dst_path = os.path.join(temp_dir, item)
                if os.path.isfile(src_path):
                    shutil.copy2(src_path, dst_path)
                elif os.path.isdir(src_path):
                    shutil.copytree(src_path, dst_path)

            # requirements.txtが存在する場合は依存関係をインストール
            requirements_file = os.path.join(lambda_dir, "requirements.txt")
            if os.path.exists(requirements_file):
                install_dependencies(requirements_file, temp_dir)

            # ZIPファイルを作成
            if output_file is None:
                output_file = os.path.join(output_dir, f"{os.path.basename(lambda_dir)}.zip")
            zip_path = create_zip_file(temp_dir, output_file)

            logger.info(f"Successfully packaged Lambda function: {os.path.basename(lambda_dir)}")
            return zip_path

        finally:
            # 一時ディレクトリを削除
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                logger.info(f"Cleaned up temporary directory: {temp_dir}")

    except Exception as e:
        logger.error(f"Error packaging Lambda function {lambda_dir}: {e}")
        raise

def main():
    """メイン関数"""
    try:
        # スクリプトのディレクトリを取得
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(script_dir))
        
        # Lambda関数のディレクトリと出力ファイル名のマッピング
        lambda_mappings = {
            "get_prices_lambda": "lambda_function.zip",
            "predict_prices_lambda": "predict_prices_lambda.zip",
            "compare_prices_lambda": "compare_prices_lambda.zip",
            "line_notification_lambda": "line_notification_lambda.zip",
            "deployment_verification_lambda": "deployment_verification.zip",
            "smoke_test_lambda": "smoke_test.zip",
            "save_price_history_lambda": "save_price_history.zip",
            "get_price_history_lambda": "get_price_history.zip",
            "check_prices_lambda": "check_prices.zip"
        }
        
        # 出力ディレクトリをterraformディレクトリに設定
        output_dir = os.path.join(project_root, "terraform")
        os.makedirs(output_dir, exist_ok=True)
        
        # 既存のZIPファイルをクリーンアップ
        logger.info("Cleaning up existing ZIP files...")
        for file in os.listdir(output_dir):
            if file.endswith('.zip'):
                file_path = os.path.join(output_dir, file)
                try:
                    os.remove(file_path)
                    logger.info(f"Removed existing ZIP file: {file}")
                except Exception as e:
                    logger.warning(f"Failed to remove {file}: {e}")
        
        # 各Lambda関数をパッケージ化
        logger.info("Starting Lambda function packaging...")
        for lambda_dir_name, output_file in lambda_mappings.items():
            lambda_dir = os.path.join(project_root, "lambdas", lambda_dir_name)
            if os.path.exists(lambda_dir):
                output_path = os.path.join(output_dir, output_file)
                try:
                    package_lambda_function(lambda_dir, output_dir, output_path)
                    logger.info(f"Successfully packaged {lambda_dir_name} to {output_file}")
                except Exception as e:
                    logger.error(f"Failed to package {lambda_dir_name}: {e}")
                    raise
            else:
                logger.error(f"Lambda directory not found: {lambda_dir}")
                raise FileNotFoundError(f"Lambda directory not found: {lambda_dir}")
        
        # 生成されたZIPファイルの検証
        logger.info("Validating generated ZIP files...")
        missing_files = []
        corrupted_files = []
        
        for output_file in lambda_mappings.values():
            zip_path = os.path.join(output_dir, output_file)
            if not os.path.exists(zip_path):
                missing_files.append(output_file)
                continue
            
            if not zipfile.is_zipfile(zip_path):
                corrupted_files.append(output_file)
        
        if missing_files:
            raise FileNotFoundError(f"Missing ZIP files: {', '.join(missing_files)}")
        
        if corrupted_files:
            raise ValueError(f"Corrupted ZIP files: {', '.join(corrupted_files)}")
        
        logger.info("All Lambda functions packaged and validated successfully")

    except Exception as e:
        logger.error(f"Error in main function: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 