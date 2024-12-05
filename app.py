import json
import logging
import os
import re
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, send_from_directory
from playwright.sync_api import sync_playwright

from config import config

load_dotenv()  # .envファイルをロード

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

    @app.route('/static/favicon.ico')
    def favicon():
        try:
            favicon_path = os.path.join(app.root_path, 'static')
            app.logger.debug(f"Favicon path: {favicon_path}")  # パスを確認
            return send_from_directory(
                favicon_path,
                'favicon.ico',
                mimetype='image/vnd.microsoft.icon'
            )
        except Exception as e:
            app.logger.error(f"Favicon error: {str(e)}")  # エラーの詳細を確認
            return '', 204

    return app

# アプリケーションインスタンスの作成
app = create_app()

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
        'iPhone 16 Pro': {},
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
                    
                    # モデル名からシリーズを判定
                    if 'Pro Max' in model_name:
                        series = 'iPhone 16 Pro Max'
                    elif 'Pro' in model_name:
                        series = 'iPhone 16 Pro'
                    elif '16' in model_name:
                        series = 'iPhone 16'
                    else:
                        continue
                    
                    # 容量を抽出（例: "128GB" または "1TB"）
                    capacity_match = re.search(r'(\d+)(GB|TB)', model_name)
                    if not capacity_match:
                        continue
                    capacity = capacity_match.group(0)  # "128GB" or "1TB"
                    
                    price_element = item.query_selector('.td.td2 .td2wrap')
                    price_text = price_element.inner_text().strip() if price_element else ""

                    if model_name and price_text and '円' in price_text:
                        # カラーを抽出（黒、白、桃、緑、青、金、灰など）
                        color_match = re.search(r'(黒|白|桃|緑|青|金|灰)', model_name)
                        color = color_match.group(1) if color_match else "不明"
                        
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

@app.route('/')
def home():
    try:
        # データベース接続
        conn = psycopg2.connect(
            host="dpg-ct8or1a3esus7384jdbg-a.oregon-postgres.render.com",
            database="official_prices_db_gop6",
            user="official_prices_db_gop6_user",
            password="ngVU5yXdsM8AMyt0Jy2FdC2fOtfL9Rc0"
        )
        cursor = conn.cursor()

        # データベースから公式価格を取得
        cursor.execute("SELECT product_name, capacity, color, price FROM official_prices;")
        official_prices = cursor.fetchall()

        # データベース接続を閉じる
        cursor.close()
        conn.close()

        # テンプレートにデータを渡して表示
        return render_template('index.html', prices=official_prices)
    except Exception as e:
        app.logger.error(f"価格取得エラー: {str(e)}")
        return render_template('error.html', error_message=str(e))

@app.route('/get_prices')
def get_prices():
    try:
        kaitori_prices = get_kaitori_prices()
        
        # データベースから公式価格を取得（colorも含める）
        conn = psycopg2.connect(
            host="dpg-ct8or1a3esus7384jdbg-a.oregon-postgres.render.com",
            database="official_prices_db_gop6",
            user="official_prices_db_gop6_user",
            password="ngVU5yXdsM8AMyt0Jy2FdC2fOtfL9Rc0"
        )
        cursor = conn.cursor()
        cursor.execute("SELECT product_name, capacity, color, price FROM official_prices;")
        official_prices = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # 公式価格をディクショナリに変換（色ごとの価格を保持）
        official_prices_dict = {}
        for row in official_prices:
            product_name, capacity, color, price = row
            if product_name not in official_prices_dict:
                official_prices_dict[product_name] = {}
            if capacity not in official_prices_dict[product_name]:
                official_prices_dict[product_name][capacity] = {}
            official_prices_dict[product_name][capacity][color] = price

        # 買取価格データに公式価格を追加
        for series in kaitori_prices:
            for capacity, details in kaitori_prices[series].items():
                # 各容量の全色の価格を取得
                color_prices = official_prices_dict.get(series, {}).get(capacity, {})
                if color_prices:
                    # 最も一般的な価格を公式価格として使用
                    official_price = list(color_prices.values())[0]
                    details['official_price'] = official_price

                    # 収支（最小～最大）を計算
                    details['profit_min'] = details['kaitori_price_min'] - official_price
                    details['profit_max'] = details['kaitori_price_max'] - official_price
                else:
                    details['official_price'] = None
                    details['profit_min'] = None
                    details['profit_max'] = None
        
        return jsonify(kaitori_prices)
    except Exception as e:
        app.logger.error(f"価格取得エラー: {str(e)}")
        return jsonify({"error": str(e)}), 500
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))

@app.errorhandler(Exception)
def handle_exception(e):
    response = {
        "error": str(e),
        "message": "An internal error occurred. Please try again later."
    }
    return jsonify(response), 500
