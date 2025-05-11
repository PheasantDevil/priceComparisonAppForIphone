#!/usr/bin/env python3

"""
使用方法:
このスクリプトは、Terraformのデプロイメント時にDynamoDBテーブルに初期データを投入するために使用されます。
以下のコマンドで実行します：
    python3 load_dynamodb_data.py

必要な環境変数:
- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY
- AWS_DEFAULT_REGION

投入されるデータ:
- official_prices.json: 公式価格データ
- price_history.json: 価格履歴データ
- price_predictions.json: 価格予測データ
- kaitori-rudea_sample-prices.json: 買取価格データ
"""

import json
import logging
import os
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import boto3

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_json_file(file_path):
    """JSONファイルを読み込む"""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading {file_path}: {str(e)}")
        raise

def write_to_official_prices(table, data):
    """公式価格データをDynamoDBに書き込む"""
    try:
        for series, capacities in data.items():
            for capacity, details in capacities.items():
                item = {
                    'series': series,
                    'capacity': capacity,
                    'colors': details['colors'],
                    'timestamp': datetime.now().isoformat()
                }
                table.put_item(Item=item)
                logger.info(f"Added {series} {capacity} to official_prices")
    except Exception as e:
        logger.error(f"Error writing to official_prices: {str(e)}")
        raise

def write_to_price_history(table, data):
    """価格履歴データをDynamoDBに書き込む"""
    try:
        for model, model_data in data.items():
            for price_data in model_data['prices']:
                item = {
                    'model': model,
                    'timestamp': int(price_data['timestamp']),
                    'price': price_data['price'],
                    'source': price_data['source']
                }
                table.put_item(Item=item)
                logger.info(f"Added price history for {model}")
    except Exception as e:
        logger.error(f"Error writing to price_history: {str(e)}")
        raise

def write_to_price_predictions(table, data):
    """
    Inserts price prediction data into the DynamoDB price_predictions table.
    
    Each prediction entry includes the series name, timestamp, predicted price, confidence score as a string, and contributing factors. Raises an exception if insertion fails.
    """
    try:
        for series, series_data in data.items():
            for prediction in series_data['predictions']:
                item = {
                    'series': series,
                    'timestamp': str(prediction['timestamp']),
                    'predicted_price': int(prediction['predicted_price']),
                    # Preserve Number type. DynamoDB needs `Decimal` or an int/float.
                    'confidence': Decimal(str(prediction['confidence'])),
                    'factors': prediction['factors']
                }
                table.put_item(Item=item)
                logger.info(f"Added price prediction for {series}")
    except Exception as e:
        logger.error(f"Error writing to price_predictions: {str(e)}")
        raise

def write_to_kaitori_prices(table, data):
    """買取価格データをDynamoDBに書き込む"""
    try:
        for model, capacities in data.items():
            for capacity, details in capacities.items():
                for color, price in details['colors'].items():
                    item = {
                        'model': model,
                        'capacity': capacity,
                        'color': color,
                        'price': price,
                        'source': details['source'],
                        'timestamp': datetime.now().isoformat()
                    }
                    table.put_item(Item=item)
                    logger.info(f"Added kaitori price for {model} {capacity} {color}")
    except Exception as e:
        logger.error(f"Error writing to kaitori_prices: {str(e)}")
        raise

def main():
    try:
        # データディレクトリのパスを設定
        data_dir = Path(__file__).parent.parent.parent / 'data'
        
        # DynamoDBクライアントの初期化
        dynamodb = boto3.resource('dynamodb')
        
        # 各テーブルの取得
        official_prices_table = dynamodb.Table('official_prices')
        price_history_table = dynamodb.Table('price_history')
        price_predictions_table = dynamodb.Table('price_predictions')
        kaitori_prices_table = dynamodb.Table('kaitori_prices')
        
        # データの読み込み
        logger.info("Loading data files...")
        official_prices = load_json_file(data_dir / 'official_prices.json')
        price_history = load_json_file(data_dir / 'price_history.json')
        price_predictions = load_json_file(data_dir / 'price_predictions.json')
        kaitori_prices = load_json_file(data_dir / 'kaitori-rudea_sample-prices.json')
        
        # データの書き込み
        logger.info("Writing data to DynamoDB...")
        write_to_official_prices(official_prices_table, official_prices)
        write_to_price_history(price_history_table, price_history)
        write_to_price_predictions(price_predictions_table, price_predictions)
        write_to_kaitori_prices(kaitori_prices_table, kaitori_prices)
        
        logger.info("Data loading completed successfully!")
        
    except Exception as e:
        logger.error(f"Error in main process: {str(e)}")
        raise

if __name__ == "__main__":
    main() 