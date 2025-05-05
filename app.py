import json
import logging
import os
import re
from datetime import datetime

import boto3
from flask import Flask, jsonify, render_template, request, send_from_directory
from playwright.sync_api import sync_playwright

from config import config
from services.dynamodb_service import get_prices_by_series


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
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # DynamoDBの設定
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('price_history')

    # Lambdaクライアントの設定
    lambda_client = boto3.client('lambda')

    @app.route("/favicon.ico")
    def favicon():
        try:
            return send_from_directory(
                os.path.join(app.root_path, "static"),
                "favicon.ico",
                mimetype="image/vnd.microsoft.icon"
            )
        except Exception as e:
            app.logger.error(f"Favicon error: {str(e)}")
            return "", 204  # No Content

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/set-alert', methods=['POST'])
    def set_alert():
        try:
            data = request.get_json()
            threshold = data.get('threshold')
            
            if not threshold:
                return jsonify({'error': '閾値が指定されていません'}), 400
            
            # 閾値をDynamoDBに保存
            table.put_item(
                Item={
                    'id': 'alert_threshold',
                    'threshold': int(threshold),
                    'timestamp': str(datetime.now())
                }
            )
            
            return jsonify({'message': 'アラートを設定しました'}), 200
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/check-prices', methods=['GET'])
    def check_prices():
        try:
            # 価格データを取得
            response = table.scan()
            items = response.get('Items', [])
            
            # アラート閾値を取得
            alert_response = table.get_item(Key={'id': 'alert_threshold'})
            threshold = alert_response.get('Item', {}).get('threshold')
            
            if not threshold:
                return jsonify({'message': 'アラート閾値が設定されていません'}), 200
            
            # 価格が閾値を下回っているかチェック
            for item in items:
                if item.get('price', float('inf')) < threshold:
                    # LINE通知を送信
                    lambda_client.invoke(
                        FunctionName='line_notification_lambda',
                        InvocationType='Event',
                        Payload=json.dumps({
                            'message': f'価格アラート: {item.get("model")}の価格が{threshold}円を下回りました。現在の価格: {item.get("price")}円'
                        })
                    )
            
            return jsonify({'message': '価格チェックを完了しました'}), 200
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return app

# アプリケーションインスタンスの作成
app = create_app()

def price_text_to_int(price_text):
    """価格テキストを整数に変換する"""
    try:
        # "123,456円" → 123456
        return int(price_text.replace("円", "").replace(",", ""))
    except (ValueError, AttributeError):
        return 0

def get_kaitori_prices():
    """買取価格データをスクレイピングで取得"""
    all_product_details = {
        "iPhone 16": {},
        "iPhone 16 Pro": {},
        "iPhone 16 Pro Max": {},
        "iPhone 16e": {},
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(chromium_sandbox=False)
        page = browser.new_page()

        for url in config.scraper.KAITORI_RUDEA_URLS:
            page.goto(url)
            page.wait_for_load_state("networkidle")

            items = page.query_selector_all(".tr")

            for item in items:
                try:
                    model_element = item.query_selector(".ttl h2")
                    model_name = model_element.inner_text().strip() if model_element else ""

                    # モデル名からシリーズを判定
                    if "Pro Max" in model_name:
                        series = "iPhone 16 Pro Max"
                    elif "Pro" in model_name:
                        series = "iPhone 16 Pro"
                    elif "16" in model_name:
                        series = "iPhone 16"
                    elif "16" in model_name:
                        series = "iPhone 16 e"
                    else:
                        continue

                    # 容量を抽出（例: "128GB" または "1TB"）
                    capacity_match = re.search(r"(\d+)(GB|TB)", model_name)
                    if not capacity_match:
                        continue
                    capacity = capacity_match.group(0)  # "128GB" or "1TB"

                    price_element = item.query_selector(".td.td2 .td2wrap")
                    price_text = price_element.inner_text().strip() if price_element else ""

                    if model_name and price_text and "円" in price_text:
                        # カラーを抽出
                        color_match = re.search(r"(黒|白|桃|緑|青|金|灰)", model_name)
                        color = color_match.group(1) if color_match else "不明"

                        # 容量ごとのデータを初期化・更新
                        if capacity not in all_product_details[series]:
                            all_product_details[series][capacity] = {
                                "colors": {},
                                "kaitori_price_min": None,
                                "kaitori_price_max": None,
                            }

                        # 色ごとの価格を保存
                        price_value = price_text_to_int(price_text)
                        all_product_details[series][capacity]["colors"][color] = {
                            "price_text": price_text,
                            "price_value": price_value,
                        }

                        # 最小・最大価格を更新
                        current_min = all_product_details[series][capacity]["kaitori_price_min"]
                        current_max = all_product_details[series][capacity]["kaitori_price_max"]

                        if current_min is None or price_value < current_min:
                            all_product_details[series][capacity]["kaitori_price_min"] = price_value
                        if current_max is None or price_value > current_max:
                            all_product_details[series][capacity]["kaitori_price_max"] = price_value

                except Exception as e:
                    app.logger.error(f"データ取得エラー: {str(e)}")
                    continue

        browser.close()

    return all_product_details

@app.route("/get_prices")
def get_prices():
    """買取価格と公式価格を取得して統合"""
    try:
        kaitori_prices = get_kaitori_prices()
        official_prices = get_prices_by_series()  # DynamoDBから公式価格を取得

        # データ統合処理
        for series, capacities in kaitori_prices.items():
            if series in official_prices:
                for capacity, details in capacities.items():
                    if capacity in official_prices[series]:
                        official_price = min(official_prices[series][capacity].values())
                        details["official_price"] = official_price
                        details["profit_min"] = details["kaitori_price_min"] - official_price
                        details["profit_max"] = details["kaitori_price_max"] - official_price

        return jsonify(kaitori_prices), 200

    except Exception as e:
        app.logger.error(f"エラー: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
