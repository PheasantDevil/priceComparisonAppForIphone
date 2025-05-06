#!/usr/bin/env python3

import json
import logging
import os
from datetime import datetime
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
    """買取価格の履歴データをDynamoDBに書き込む"""
    try:
        for model, model_data in data.items():
            for price_data in model_data['prices']:
                # kaitoriの価格のみを保存
                if price_data['source'] == 'kaitori':
                    item = {
                        'model': model,
                        'timestamp': price_data['timestamp'],
                        'price': price_data['price'],
                        'source': price_data['source']
                    }
                    table.put_item(Item=item)
                    logger.info(f"Added kaitori price history for {model}")
    except Exception as e:
        logger.error(f"Error writing to price_history: {str(e)}")
        raise

def write_to_price_predictions(table, data):
    """価格予測データをDynamoDBに書き込む"""
    try:
        for series, series_data in data.items():
            for prediction in series_data['predictions']:
                item = {
                    'series': series,
                    'timestamp': prediction['timestamp'],
                    'predicted_price': prediction['predicted_price'],
                    'confidence': prediction['confidence'],
                    'factors': prediction['factors']
                }
                table.put_item(Item=item)
                logger.info(f"Added price prediction for {series}")
    except Exception as e:
        logger.error(f"Error writing to price_predictions: {str(e)}")
        raise

def main():
    try:
        # プロジェクトのルートディレクトリを取得
        project_root = Path(__file__).parent.parent
        data_dir = project_root / 'data'
        
        # データディレクトリの存在確認
        if not data_dir.exists():
            raise FileNotFoundError(f"Data directory not found: {data_dir}")
        
        # DynamoDBクライアントの初期化
        dynamodb = boto3.resource('dynamodb')
        
        # 各テーブルの取得
        official_prices_table = dynamodb.Table('official_prices')
        price_history_table = dynamodb.Table('price_history')
        price_predictions_table = dynamodb.Table('price_predictions')
        
        # データの読み込み
        logger.info("Loading data files...")
        official_prices = load_json_file(data_dir / 'official_prices.json')
        price_history = load_json_file(data_dir / 'price_history.json')
        price_predictions = load_json_file(data_dir / 'price_predictions.json')
        
        # データの書き込み
        logger.info("Writing data to DynamoDB...")
        write_to_official_prices(official_prices_table, official_prices)
        write_to_price_history(price_history_table, price_history)
        write_to_price_predictions(price_predictions_table, price_predictions)
        
        logger.info("Data loading completed successfully!")
        
    except Exception as e:
        logger.error(f"Error in main process: {str(e)}")
        raise

if __name__ == "__main__":
    main() 