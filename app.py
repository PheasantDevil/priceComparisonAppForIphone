import logging
import os
import re

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

def get_kaitori_prices():
    all_product_details = {}
    
    with sync_playwright() as p:
        browser = p.chromium.launch(chromium_sandbox=False)
        page = browser.new_page()
        
        for url in config.scraper.KAITORI_RUDEA_URL:
            page.goto(url, timeout=app.config['PLAYWRIGHT_TIMEOUT'])
            page.wait_for_selector('.tr', timeout=app.config['PLAYWRIGHT_TIMEOUT'])

            items = page.query_selector_all('.tr')

            for item in items:
                model_name = "不明"
                price_text = "不明"

                try:
                    model_element = item.query_selector('.ttl h2')
                    model_name = model_element.inner_text().strip()
                except Exception as e:
                    app.logger.error(f"モデル名取得エラー: {str(e)}")
                    model_name = "エラー: モデル名取得失敗"

                try:
                    price_element = item.query_selector('.td.td2 .td2wrap')
                    price_text = price_element.inner_text().strip()
                except Exception as e:
                    app.logger.error(f"価格取得エラー: {str(e)}")
                    price_text = "エラー: 買取価格取得失敗"

                if model_name and price_text and '円' in price_text:
                    series = "iPhone 16 Pro Max" if "Pro Max" in model_name else "iPhone 16"
                    if series not in all_product_details:
                        all_product_details[series] = {}
                    all_product_details[series][model_name] = price_text

        browser.close()
    
    # 容量でソート
    for series in all_product_details:
        all_product_details[series] = dict(sorted(all_product_details[series].items(), key=lambda x: get_capacity(x[0])))
    
    return all_product_details

def get_capacity(model_name):
    match = re.search(r'(\d+)GB', model_name)
    if match:
        return int(match.group(1))
    match = re.search(r'(\d+)TB', model_name)
    if match:
        return int(match.group(1)) * 1024
    return 0

# アプリケーションインスタンスの作成
app = create_app()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/get_prices')
def get_prices():
    try:
        iphone_prices = get_kaitori_prices()
        return jsonify(iphone_prices)
    except Exception as e:
        app.logger.error(f"価格取得エラー: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
