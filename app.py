import json
import logging
import os
import re
from datetime import datetime

import boto3
import requests
from flask import Flask, jsonify, render_template, request, send_from_directory
from playwright.sync_api import sync_playwright

from config import config
from services.dynamodb_service import get_prices_by_series


def create_app():
    app = Flask(__name__, static_folder='static')

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

    # API Gatewayのエンドポイント
    API_ENDPOINT = "https://qpt4qfbk57.execute-api.ap-northeast-1.amazonaws.com/production/get_prices"

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

    @app.route('/api/prices')
    def proxy_prices():
        try:
            series = request.args.get('series')
            if not series:
                return jsonify({'error': 'シリーズが指定されていません'}), 400

            # API Gatewayへのリクエスト
            upstream = requests.get(f"{API_ENDPOINT}?series={series}", timeout=5)
            return (
                jsonify(upstream.json()),
                upstream.status_code,
                {"Content-Type": upstream.headers.get("Content-Type", "application/json")},
            )
        except requests.exceptions.RequestException as e:
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
        "iPhone 16 Plus": {},
        "iPhone 16 Pro": {},
        "iPhone 16 Pro Max": {},
        "iPhone 16e": {},
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(chromium_sandbox=False)
        page = browser.new_page()

        for url in config.scraper.KAITORI_RUDEA_URLS:
            try:
                page.goto(url)
                page.wait_for_load_state("networkidle")
                app.logger.info(f"Scraping URL: {url}")

                items = page.query_selector_all(".tr")
                app.logger.info(f"Found {len(items)} items on page")

                for item in items:
                    try:
                        model_element = item.query_selector(".ttl h2")
                        model_name = model_element.inner_text().strip() if model_element else ""
                        app.logger.debug(f"Processing model: {model_name}")

                        # モデル名からシリーズを判定
                        if "Pro Max" in model_name:
                            series = "iPhone 16 Pro Max"
                        elif "Pro" in model_name:
                            series = "iPhone 16 Pro"
                        elif "Plus" in model_name:
                            series = "iPhone 16 Plus"
                        elif "16e" in model_name or "16 e" in model_name:
                            series = "iPhone 16e"
                        elif "16" in model_name:
                            series = "iPhone 16"
                        else:
                            app.logger.debug(f"Skipping unknown model: {model_name}")
                            continue

                        # 容量を抽出（例: "128GB" または "1TB"）
                        capacity_match = re.search(r"(\d+)(GB|TB)", model_name)
                        if not capacity_match:
                            app.logger.debug(f"No capacity found in model: {model_name}")
                            continue
                        
                        # 容量の正規化
                        capacity_value = int(capacity_match.group(1))
                        capacity_unit = capacity_match.group(2)
                        if capacity_unit == "TB":
                            capacity = f"{capacity_value}TB"
                        else:
                            capacity = f"{capacity_value}GB"

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

                            app.logger.debug(f"Added price data for {series} {capacity} {color}: {price_value}円")

                    except Exception as e:
                        app.logger.error(f"Error processing item: {str(e)}")
                        continue

            except Exception as e:
                app.logger.error(f"Error processing URL {url}: {str(e)}")
                continue

        browser.close()

    # 結果のログ出力
    for series, capacities in all_product_details.items():
        app.logger.info(f"Scraped data for {series}:")
        for capacity, data in capacities.items():
            app.logger.info(f"  {capacity}: min={data['kaitori_price_min']}, max={data['kaitori_price_max']}")

    return all_product_details

@app.route("/get_prices")
def get_prices():
    """DynamoDBから最新の価格情報を取得"""
    try:
        # DynamoDBから価格データを取得
        dynamodb = boto3.resource('dynamodb')
        kaitori_table = dynamodb.Table('kaitori_prices')
        official_table = dynamodb.Table('official_prices')
        
        app.logger.info("Fetching data from kaitori_prices table...")
        # 買取価格データを取得
        kaitori_response = kaitori_table.scan()
        kaitori_items = kaitori_response.get('Items', [])
        app.logger.info(f"Found {len(kaitori_items)} items in kaitori_prices table")
        
        app.logger.info("Fetching data from official_prices table...")
        # 公式価格データを取得
        official_response = official_table.scan()
        official_items = official_response.get('Items', [])
        app.logger.info(f"Found {len(official_items)} items in official_prices table")
        app.logger.debug(f"Official prices data: {json.dumps(official_items, indent=2)}")
        
        # 公式価格をマッピング
        official_prices = {}
        for item in official_items:
            series = item.get('series')
            capacity = item.get('capacity')
            colors = item.get('colors', {})
            
            if series and capacity:
                if series not in official_prices:
                    official_prices[series] = {}
                official_prices[series][capacity] = colors
        
        app.logger.debug(f"Mapped official prices: {json.dumps(official_prices, indent=2)}")
        
        # データを整形
        price_data = {}
        for item in kaitori_items:
            model = item.get('model')
            capacity = item.get('capacity')
            price = item.get('price')
            
            app.logger.debug(f"Processing kaitori item: {json.dumps(item, indent=2)}")
            
            # モデル名からシリーズを判定
            if "Pro Max" in model:
                series = "iPhone 16 Pro Max"
            elif "Pro" in model:
                series = "iPhone 16 Pro"
            elif "16e" in model:
                series = "iPhone 16e"
            elif "16" in model:
                series = "iPhone 16"
            else:
                app.logger.warning(f"Skipping unknown model: {model}")
                continue
            
            if series not in price_data:
                price_data[series] = {}
            
            if capacity not in price_data[series]:
                # 公式価格を取得
                official_colors = official_prices.get(series, {}).get(capacity, {})
                app.logger.debug(f"Found official colors for {series} {capacity}: {official_colors}")
                
                # レスポンス形式を統一
                price_data[series][capacity] = {
                    'kaitori_price': price,
                    'official_price': official_colors.get('price', 0),
                    'price_diff': price - official_colors.get('price', 0),
                    'rakuten_diff': 0  # 必要に応じて計算
                }
            else:
                # 最小・最大価格を更新
                current_price = price_data[series][capacity]['kaitori_price']
                if price > current_price:
                    price_data[series][capacity]['kaitori_price'] = price
                    price_data[series][capacity]['price_diff'] = price - price_data[series][capacity]['official_price']

        app.logger.debug(f"Final price data: {json.dumps(price_data, indent=2)}")
        return jsonify(price_data), 200

    except Exception as e:
        app.logger.error(f"エラー: {str(e)}")
        app.logger.exception("Detailed error information:")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
