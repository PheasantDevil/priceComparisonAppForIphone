import json
import logging
import os
import re
from datetime import datetime

import requests
from flask import Flask, jsonify, render_template, request, send_from_directory
from google.cloud import storage
from playwright.sync_api import sync_playwright

from config import config


def create_app():
    """
    Creates and configures the Flask application with integrated GCP services, web scraping, and API proxy routes.
    
    Initializes the Flask app with settings from the configuration, sets up logging, and configures GCP Cloud Storage.
    Defines routes for serving the favicon, rendering the index page, setting alert thresholds, checking prices with alert notifications,
    and proxying price data requests to an external Cloud Run endpoint.
    """
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

    # Cloud Storageクライアントの初期化
    storage_client = storage.Client()
    bucket = storage_client.bucket(os.getenv('BUCKET_NAME', 'price-comparison-app-data'))

    # Cloud Runのエンドポイント
    API_ENDPOINT = os.getenv('CLOUD_RUN_ENDPOINT', 'https://us-central1-price-comparison-app-463007.cloudfunctions.net/get-prices')

    @app.route("/favicon.ico")
    def favicon():
        """
        Serves the favicon.ico file from the assets directory.
        
        Returns:
            The favicon.ico file with the appropriate MIME type, or an empty response with
            HTTP 204 status if an error occurs.
        """
        try:
            return send_from_directory(
                os.path.join(app.root_path, "assets"),
                "favicon.ico",
                mimetype="image/vnd.microsoft.icon"
            )
        except Exception as e:
            app.logger.error(f"Favicon error: {str(e)}")
            return "", 204  # No Content

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/health')
    def health_check():
        """ヘルスチェックエンドポイント"""
        return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()}), 200

    @app.route('/set-alert', methods=['POST'])
    def set_alert():
        try:
            data = request.get_json()
            threshold = data.get('threshold')
            
            if not threshold:
                return jsonify({'error': '閾値が指定されていません'}), 400
            
            # 閾値をCloud Storageに保存
            alert_blob = bucket.blob('config/alert_threshold.json')
            alert_data = {
                'threshold': int(threshold),
                'timestamp': datetime.now().isoformat()
            }
            alert_blob.upload_from_string(
                json.dumps(alert_data),
                content_type='application/json'
            )
            
            return jsonify({'message': 'アラートを設定しました'}), 200
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/check-prices', methods=['GET'])
    def check_prices():
        """
        Checks price data against an alert threshold and triggers notifications if prices fall below it.
        
        Retrieves all price records and the configured alert threshold from Cloud Storage.
        For each price below the threshold, triggers a Cloud Function to send a LINE notification.
        Returns a completion message or an error response.
        """
        try:
            # 価格データを取得
            current_date = datetime.now().strftime('%Y/%m/%d')
            prices_blob = bucket.blob(f'prices/{current_date}/prices.json')
            prices_data = json.loads(prices_blob.download_as_string())
            
            # アラート閾値を取得
            alert_blob = bucket.blob('config/alert_threshold.json')
            alert_data = json.loads(alert_blob.download_as_string())
            threshold = alert_data.get('threshold')
            
            if not threshold:
                return jsonify({'message': 'アラート閾値が設定されていません'}), 200
            
            # 価格が閾値を下回っているかチェック
            for series, capacities in prices_data.items():
                for capacity, data in capacities.items():
                    if data.get('kaitori_price_min', float('inf')) < threshold:
                        # LINE通知を送信
                        notification_url = f"{API_ENDPOINT}/notify"
                        requests.post(
                            notification_url,
                            json={
                                'message': f'価格アラート: {series} {capacity}の価格が{threshold}円を下回りました。現在の価格: {data.get("kaitori_price_min")}円'
                            }
                        )
            
            return jsonify({'message': '価格チェックを完了しました'}), 200
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/prices')
    def proxy_prices():
        """
        Proxies a price data request to an external Cloud Run endpoint based on the provided series.
        
        Validates the presence of the 'series' query parameter, forwards the request to the external API,
        and returns the JSON response. Returns an error message with an appropriate status code if the
        parameter is missing or if the external request fails.
        """
        try:
            series = request.args.get('series')
            if not series:
                return jsonify({'error': 'シリーズが指定されていません'}), 400

            # Cloud Runへのリクエスト
            upstream = requests.get(f"{API_ENDPOINT}/prices?series={series}", timeout=5)
            return (
                jsonify(upstream.json()),
                upstream.status_code,
                {"Content-Type": upstream.headers.get("Content-Type", "application/json")},
            )
        except requests.exceptions.RequestException as e:
            return jsonify({'error': str(e)}), 500

    @app.route("/get_prices")
    def get_prices():
        """
        Retrieves and aggregates the latest buyback and official price data from Cloud Storage.
        
        Returns:
            A JSON response with the aggregated price data and HTTP status 200 on success,
            or an error message with HTTP status 500 on failure.
        """
        try:
            storage_client = storage.Client()
            bucket = storage_client.bucket(os.getenv('BUCKET_NAME', 'price-comparison-app-data'))
            current_date = datetime.now().strftime('%Y/%m/%d')
            kaitori_blob = bucket.blob(f'prices/{current_date}/prices.json')
            kaitori_data = json.loads(kaitori_blob.download_as_string())
            app.logger.info(f"Found {len(kaitori_data)} items in prices.json")
            official_blob = bucket.blob('config/official_prices.json')
            official_data = json.loads(official_blob.download_as_string())
            app.logger.info(f"Found {len(official_data)} items in official_prices.json")
            app.logger.debug(f"Official prices data: {json.dumps(official_data, indent=2)}")

            # series/pricesネスト形式で整形
            response = {}
            for item in kaitori_data:
                series = item.get('series')
                capacity = item.get('capacity')
                kaitori_price_min = item.get('kaitori_price_min', 0)
                if not series or not capacity:
                    continue
                if series not in response:
                    response[series] = {
                        'series': series,
                        'prices': {}
                    }
                # 公式価格
                official_price = official_data.get(series, {}).get(capacity, {}).get('price', 0)
                # 差額
                price_diff = kaitori_price_min - official_price
                # rakuten_diffは現状0固定
                response[series]['prices'][capacity] = {
                    'official_price': official_price,
                    'kaitori_price': kaitori_price_min,
                    'price_diff': price_diff,
                    'rakuten_diff': 0
                }
            app.logger.debug(f"Final price data: {json.dumps(response, indent=2)}")
            return jsonify(response), 200
        except Exception as e:
            app.logger.error(f"エラー: {str(e)}")
            app.logger.exception("Detailed error information:")
            return jsonify({"error": str(e)}), 500

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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
