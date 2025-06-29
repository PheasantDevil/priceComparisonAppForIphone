import json
import logging
import os
import sys
from datetime import datetime, timedelta

import functions_framework
import requests
from google.cloud import firestore
from google.oauth2 import service_account

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
        
        # Firestoreクライアントの初期化
        db = firestore.Client()
        
        # 現在の買取価格を取得
        kaitori_docs = db.collection('kaitori_prices').stream()
        
        saved_count = 0
        for doc in kaitori_docs:
            data = doc.to_dict()
            series = data.get('series')
            capacity = data.get('capacity')
            kaitori_price_min = data.get('kaitori_price_min', 0)
            kaitori_price_max = data.get('kaitori_price_max', 0)
            colors = data.get('colors', {})
            
            if series and capacity and kaitori_price_min > 0:
                # 価格履歴を保存
                current_timestamp = int(datetime.now().timestamp())
                expiration_time = int((datetime.now() + timedelta(days=14)).timestamp())
                
                history_data = {
                    'series': series,
                    'capacity': capacity,
                    'kaitori_price_min': kaitori_price_min,
                    'kaitori_price_max': kaitori_price_max,
                    'colors': colors,
                    'timestamp': current_timestamp,
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'expiration_time': expiration_time,
                    'source': 'kaitori-rudea'
                }
                
                # Firestoreに保存
                doc_ref = db.collection('price_history').document()
                doc_ref.set(history_data)
                saved_count += 1
                logger.info(f"Saved price history: {series} {capacity} - min: {kaitori_price_min}, max: {kaitori_price_max}")
        
        # 古いデータをクリーンアップ（2週間以上前）
        cutoff_timestamp = int((datetime.now() - timedelta(days=14)).timestamp())
        query = (
            db.collection('price_history')
            .where('timestamp', '<', cutoff_timestamp)
        )
        
        docs = query.stream()
        deleted_count = 0
        
        for doc in docs:
            doc.reference.delete()
            deleted_count += 1
        
        logger.info(f"Successfully processed {saved_count} price history records and deleted {deleted_count} old records")
        
        return (json.dumps({
            'status': 'success',
            'message': f'価格履歴保存バッチが正常に完了しました。保存: {saved_count}件, 削除: {deleted_count}件'
        }), 200, headers)
            
    except Exception as e:
        logger.error(f"エラーが発生しました: {str(e)}")
        return (json.dumps({
            'status': 'error',
            'message': f'エラーが発生しました: {str(e)}'
        }), 500, headers)
