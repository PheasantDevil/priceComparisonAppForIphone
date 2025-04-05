import logging
import time

import boto3
from botocore.exceptions import ClientError

# ロガーの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def delete_api_with_retry(apigw, api, max_retries=5, initial_wait=5):
    """指数バックオフを使用してAPIを削除する"""
    for attempt in range(max_retries):
        try:
            apigw.delete_rest_api(restApiId=api['id'])
            logger.info(f"Successfully deleted API: {api['name']}")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'TooManyRequestsException':
                wait_time = initial_wait * (2 ** attempt)  # 指数バックオフ
                if attempt < max_retries - 1:
                    logger.warning(f"Rate limit reached. Waiting {wait_time} seconds before retry {attempt + 1}/{max_retries}...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to delete API {api['name']} after {max_retries} retries")
                    return False
            else:
                logger.error(f"Error deleting API {api['name']}: {str(e)}")
                return False
        except Exception as e:
            logger.error(f"Unexpected error deleting API {api['name']}: {str(e)}")
            return False
    return False

def cleanup_api_gateway():
    try:
        # API Gatewayクライアントの作成
        apigw = boto3.client('apigateway')
        
        # 既存のAPIを取得
        apis = apigw.get_rest_apis()['items']
        logger.info(f"Found {len(apis)} APIs")
        
        # 現在使用中のAPIを除外
        current_api_id = 'l8l7v5xw9d'  # 現在使用中のAPI ID
        apis_to_delete = [api for api in apis if api['id'] != current_api_id]
        
        logger.info(f"Deleting {len(apis_to_delete)} old APIs")
        
        # 各APIを削除
        success_count = 0
        failed_apis = []
        
        for api in apis_to_delete:
            logger.info(f"Deleting API: {api['name']} (ID: {api['id']})")
            if delete_api_with_retry(apigw, api):
                success_count += 1
                time.sleep(3)  # 成功後も少し待機
            else:
                failed_apis.append(api)
        
        # 結果の表示
        logger.info(f"Cleanup completed. Successfully deleted {success_count} APIs.")
        if failed_apis:
            logger.warning(f"Failed to delete {len(failed_apis)} APIs:")
            for api in failed_apis:
                logger.warning(f"  - {api['name']} (ID: {api['id']})")
    
    except Exception as e:
        logger.error(f"Error during API Gateway cleanup: {str(e)}")

if __name__ == "__main__":
    cleanup_api_gateway() 