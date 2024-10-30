import json
import logging
import os
import re
from pathlib import Path

from flask import Flask, jsonify, render_template
from playwright.sync_api import sync_playwright

from config import config


def create_app():
    app = Flask(__name__)
    
    # アプリケーション設定の適用
    app.config['DEBUG'] = config.app.DEBUG
    app.config['SECRET_KEY'] = config.app.SECRET_KEY
    
    # Playwrightのタイムアウト設定
    app.config['PLAYWRIGHT_TIMEOUT'] = config.scraper.REQUEST_TIMEOUT * 1000  # ミリ秒単位に変換
    
    # ログ設定
    logging.basicConfig(
        level=getattr(logging, config.app.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    return app

def load_official_prices():
    """公式価格データをJSONファイルから読み込む"""
    try:
        json_path = Path(__file__).parent / 'data' / 'official_prices.json'
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        app.logger.error(f"公式価格データの読み込みエラー: {str(e)}")
        return {}

def price_text_to_int(price_text):
    """価格テキストを整数に変換する"""
    try:
        # "123,456円" → 123456
        return int(price_text.replace('円', '').replace(',', ''))
    except (ValueError, AttributeError):
        return 0

def get_kaitori_prices():
    all_product_details = {
        'iPhone 16': {},
        'iPhone 16 Pro Max': {}
    }
    
    with sync_playwright() as p:
        browser = p.chromium.launch(chromium_sandbox=False)
        page = browser.new_page()
        
        for url in config.scraper.KAITORI_RUDEA_URLS:
            page.goto(url)
            page.wait_for_load_state('networkidle')

            items = page.query_selector_all('.tr')
            
            for item in items:
                try:
                    model_element = item.query_selector('.ttl h2')
                    model_name = model_element.inner_text().strip() if model_element else ""
                    
                    price_element = item.query_selector('.td.td2 .td2wrap')
                    price_text = price_element.inner_text().strip() if price_element else ""

                    if model_name and price_text and '円' in price_text:
                        # モデル名から容量を抽出
                        capacity_match = re.search(r'(\d+)(GB|TB)', model_name)
                        if not capacity_match:
                            continue
                            
                        capacity = f"{capacity_match.group(1)}{capacity_match.group(2)}"
                        
                        # カラーを抽出（黒、白、桃、緑、青、金、灰など）
                        color_match = re.search(r'(黒|白|桃|緑|青|金|灰)', model_name)
                        color = color_match.group(1) if color_match else "不明"
                        
                        # iPhoneシリーズを判断
                        if 'Pro Max' in model_name:
                            series = 'iPhone 16 Pro Max'
                        else:
                            series = 'iPhone 16'
                            
                        # 容量ごとのデータを初期化・更新
                        if capacity not in all_product_details[series]:
                            all_product_details[series][capacity] = {
                                'colors': {},
                                'kaitori_price_min': None,
                                'kaitori_price_max': None
                            }
                        
                        # 色ごとの価格を保存
                        price_value = price_text_to_int(price_text)
                        all_product_details[series][capacity]['colors'][color] = {
                            'price_text': price_text,
                            'price_value': price_value
                        }
                        
                        # 最小・最大価格を更新
                        current_min = all_product_details[series][capacity]['kaitori_price_min']
                        current_max = all_product_details[series][capacity]['kaitori_price_max']
                        
                        if current_min is None or price_value < current_min:
                            all_product_details[series][capacity]['kaitori_price_min'] = price_value
                        if current_max is None or price_value > current_max:
                            all_product_details[series][capacity]['kaitori_price_max'] = price_value
                            
                except Exception as e:
                    app.logger.error(f"データ取得エラー: {str(e)}")
                    continue

        browser.close()
    
    return all_product_details

# アプリケーションインスタンスの作成
app = create_app()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/get_prices')
def get_prices():
    try:
        kaitori_prices = get_kaitori_prices()
        official_prices = load_official_prices()
        
        # 買取価格と公式価格を組み合わせる
        for series in kaitori_prices:
            if series in official_prices:
                for capacity, details in kaitori_prices[series].items():
                    if capacity in official_prices[series]:
                        # 最安値の公式価格を取得
                        official_price = min(official_prices[series][capacity].values())
                        details['official_price'] = official_price
                        # 最大収益と最小収益を計算
                        details['profit_min'] = details['kaitori_price_min'] - official_price
                        details['profit_max'] = details['kaitori_price_max'] - official_price
                    else:
                        details['official_price'] = None
                        details['profit_min'] = None
                        details['profit_max'] = None
        
        app.logger.debug(f"取得した価格データ: {kaitori_prices}")
        return jsonify(kaitori_prices)
    except Exception as e:
        app.logger.error(f"価格取得エラー: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
