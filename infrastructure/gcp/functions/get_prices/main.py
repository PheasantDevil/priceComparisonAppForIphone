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
    "iPhone 16 Plus": ["128GB", "256GB", "512GB"],
    "iPhone 16 Pro Max": ["256GB", "512GB", "1TB"],
    "iPhone 16 e": ["128GB", "256GB", "512GB"]
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
        # 公式価格の取得（Firestoreから）
        official_doc = db.collection('official_prices').document(series).get()
        official_data = official_doc.to_dict() if official_doc.exists else {}

        logger.info(f"Getting kaitori prices from Firestore for series: {series}")
        # 買取価格の取得（Firestoreから）
        kaitori_docs = db.collection('kaitori_prices').where('series', '==', series).stream()
        kaitori_items = [doc.to_dict() for doc in kaitori_docs]
        logger.info(f"Retrieved {len(kaitori_items)} kaitori price items from Firestore")

        # 容量ごとに買取価格をマッピング
        kaitori_map = {item['capacity']: item for item in kaitori_items}

        prices = {}
        for capacity in VALID_CAPACITIES.get(series, []):
            # 公式価格
            official_price = 0
            if 'price' in official_data and capacity in official_data['price']:
                official_price_info = official_data['price'][capacity]
                if isinstance(official_price_info, dict) and 'colors' in official_price_info:
                    color_prices = official_price_info['colors']
                    if color_prices:
                        official_price = safe_int(next(iter(color_prices.values())))
                else:
                    official_price = safe_int(official_price_info)

            # 買取価格（Firestoreから取得）
            kaitori_price = 0
            kaitori_item = kaitori_map.get(capacity)
            if kaitori_item:
                kaitori_price = safe_int(kaitori_item.get('kaitori_price_min', 0))

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

def get_price_history(request):
    """
    Cloud Function handler that retrieves price history for graph display.
    
    Processes an incoming HTTP request, validates the requested iPhone series and capacity,
    retrieves price history for the specified period, and returns the data in JSON format
    with appropriate CORS headers.
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
        logger.info("Starting price history retrieval process")
        
        # クエリパラメータからシリーズと容量を取得
        series = request.args.get('series', 'iPhone 16')
        capacity = request.args.get('capacity', '128GB')
        days = int(request.args.get('days', '14'))
        
        logger.info(f"Retrieving price history for series: {series}, capacity: {capacity}, days: {days}")
        
        # シリーズが有効かチェック
        if series not in VALID_CAPACITIES:
            return (json.dumps({
                'message': f'Invalid series: {series}. Valid series are: {", ".join(VALID_CAPACITIES.keys())}'
            }), 400, headers)
        
        # 容量が有効かチェック
        if capacity not in VALID_CAPACITIES.get(series, []):
            return (json.dumps({
                'message': f'Invalid capacity: {capacity}. Valid capacities for {series} are: {", ".join(VALID_CAPACITIES.get(series, []))}'
            }), 400, headers)
        
        # 価格履歴を取得
        history_data = fetch_price_history(series, capacity, days)
        logger.info(f"Retrieved {len(history_data)} price history records")
        
        return (json.dumps({
            'series': series,
            'capacity': capacity,
            'days': days,
            'history': history_data
        }), 200, headers)
        
    except Exception as e:
        logger.error(f"Error in get_price_history: {str(e)}", exc_info=True)
        return (json.dumps({'message': 'Internal server error', 'error': str(e)}), 500, headers)

def fetch_price_history(series, capacity, days):
    """
    Retrieves price history for graph display.
    
    Fetches price history from Firestore for the specified series, capacity, and time period.
    Returns a list of price history records sorted by date.
    
    Args:
        series: The iPhone series name
        capacity: The capacity (e.g., '128GB', '1TB')
        days: Number of days to look back
    
    Returns:
        A list of price history records
    """
    try:
        from datetime import datetime, timedelta

        # 指定日数前のタイムスタンプ
        start_timestamp = int((datetime.now() - timedelta(days=days)).timestamp())
        
        # クエリ実行（インデックスを避けるため、シンプルなクエリに変更）
        query = (
            db.collection('price_history')
            .where('series', '==', series)
            .where('capacity', '==', capacity)
        )
        
        docs = query.stream()
        
        # グラフ用データに変換（クライアント側でフィルタリング）
        history_data = []
        for doc in docs:
            data = doc.to_dict()
            timestamp = data.get('timestamp', 0)
            
            # 指定日数以内のデータのみをフィルタリング
            if timestamp >= start_timestamp:
                # dateフィールドが存在しない場合はtimestampから生成
                date_str = data.get('date')
                if not date_str and timestamp:
                    from datetime import datetime
                    date_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
                
                history_data.append({
                    'date': date_str or 'Unknown',
                    'timestamp': timestamp,
                    'price_min': data.get('kaitori_price_min', 0),
                    'price_max': data.get('kaitori_price_max', 0),
                    'price_avg': (data.get('kaitori_price_min', 0) + data.get('kaitori_price_max', 0)) // 2
                })
        
        # タイムスタンプでソート
        history_data.sort(key=lambda x: x['timestamp'])
        
        return history_data
        
    except Exception as e:
        logger.error(f"Error fetching price history: {str(e)}", exc_info=True)
        return [] 