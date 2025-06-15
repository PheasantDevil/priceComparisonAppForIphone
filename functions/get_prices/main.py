import json
import logging
import os
from datetime import datetime, timezone
from decimal import Decimal

from google.cloud import firestore

# ロガーの設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Firestoreクライアントの初期化
db = firestore.Client()

# シリーズごとの有効な容量を定義
VALID_CAPACITIES = {
    "iPhone 16": ["128GB", "256GB", "512GB"],
    "iPhone 16 Pro": ["128GB", "256GB", "512GB", "1TB"],
    "iPhone 16 Pro Max": ["256GB", "512GB", "1TB"],
    "iPhone 16e": ["128GB", "256GB", "512GB"]
}

def safe_int(val):
    """
    Safely converts a numeric value to an integer.
    
    Accepts int, float, Decimal, or string representations of numbers and returns the integer value.
    """
    if val is None:
        return 0
    if isinstance(val, (int, float, Decimal)):
        return int(val)
    try:
        return int(str(val))
    except (ValueError, TypeError):
        logger.warning(f"Could not convert value to int: {val}")
        return 0

def get_prices(request):
    """
    Cloud Function handler that retrieves iPhone price information for a specified series.
    
    Processes an incoming HTTP request, validates the requested iPhone series,
    retrieves official and buyback prices for all valid capacities, and returns the
    data in JSON format with appropriate CORS headers. Returns HTTP 400 for invalid
    series and HTTP 500 for internal errors.
    """
    # CORSヘッダーの設定
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'GET,OPTIONS'
    }

    # OPTIONSリクエストの処理
    if request.method == 'OPTIONS':
        return ('', 204, headers)

    try:
        logger.info("Starting price retrieval process")
        
        # クエリパラメータからシリーズを取得
        series = request.args.get('series', 'iPhone 16')
        logger.info(f"Retrieving prices for series: {series}")
        
        # シリーズが有効かチェック
        if series not in VALID_CAPACITIES:
            return (json.dumps({
                'message': f'Invalid series: {series}. Valid series are: {", ".join(VALID_CAPACITIES.keys())}'
            }), 400, headers)
        
        # 価格情報を取得
        prices = fetch_prices(series)
        logger.info(f"Retrieved prices: {json.dumps(prices)}")
        
        return (json.dumps(prices), 200, headers)
        
    except Exception as e:
        logger.error(f"Error in get_prices: {str(e)}", exc_info=True)
        return (json.dumps({'message': 'Internal server error', 'error': str(e)}), 500, headers)

def fetch_prices(series):
    """
    Retrieves price information for all valid capacities of the specified iPhone series.
    
    Fetches official and buyback (kaitori) prices from Firestore for the given series.
    Returns a dictionary mapping each valid capacity to its official price, kaitori price,
    the difference between them, and the difference between the kaitori price and 90% of the official price.
    If data is missing for the series, returns zeroed price information for all capacities.
    
    Args:
        series: The iPhone series name to retrieve prices for.
    
    Returns:
        A dictionary with the series name and a mapping of capacities to their price details.
    """
    try:
        logger.info(f"Getting official prices for series: {series}")
        # 公式価格の取得
        official_doc = db.collection('official_prices').document(series).get()
        official_data = official_doc.to_dict() if official_doc.exists else {}

        logger.info(f"Getting kaitori prices for series: {series}")
        # 買取価格の取得
        kaitori_docs = db.collection('kaitori_prices').where('series', '==', series).stream()
        kaitori_items = [doc.to_dict() for doc in kaitori_docs]

        # 公式価格をマッピング
        official_prices = official_data.get('price', {})

        # 買取価格をマッピング
        kaitori_map = {item['capacity']: item for item in kaitori_items}

        prices = {}
        for capacity in VALID_CAPACITIES.get(series, []):
            # 公式価格
            official_price = safe_int(official_prices.get(capacity, 0))

            # 買取価格
            kaitori_price = 0
            kaitori_item = kaitori_map.get(capacity)
            if kaitori_item:
                kaitori_price = safe_int(kaitori_item.get('kaitori_price_max', 0))

            prices[capacity] = {
                'official_price': official_price,
                'kaitori_price': kaitori_price,
                'price_diff': kaitori_price - official_price,
                'rakuten_diff': kaitori_price - int(official_price * 0.9)
            }

        return {
            'series': series,
            'prices': prices
        }

    except Exception as e:
        logger.error(f"Error getting prices: {str(e)}", exc_info=True)
        raise 