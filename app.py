import json
import logging
import os
import subprocess
import sys
from datetime import datetime

from flask import Flask, jsonify, render_template, request, send_from_directory
from google.cloud import storage

# Google Cloud Storageクライアントの初期化
storage_client = None
try:
    storage_client = storage.Client()
except Exception as e:
    print(f"Warning: Could not initialize Google Cloud Storage client: {e}")

# 設定クラス
class FallbackConfig:
    class scraper:
        KAITORI_RUDEA_URLS = [
            "https://kaitori-rudeya.com/category/detail/183",
            "https://kaitori-rudeya.com/category/detail/184",
            "https://kaitori-rudeya.com/category/detail/185",
            "https://kaitori-rudeya.com/category/detail/186",
            "https://kaitori-rudeya.com/category/detail/205"
        ]
        REQUEST_TIMEOUT = 60
    
    class app:
        DEBUG = False
        SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key-for-production')
        LOG_LEVEL = 'INFO'

config = FallbackConfig()

def create_app():
    """
    Creates and configures the Flask application with integrated GCP services.
    
    Initializes the Flask app with settings from the configuration, sets up logging, and configures GCP Cloud Storage.
    Defines routes for serving the favicon, rendering the index page, and basic API endpoints.
    """
    app = Flask(__name__, static_folder='static')

    # アプリケーション設定の適用
    app.config['DEBUG'] = config.app.DEBUG
    app.config['SECRET_KEY'] = config.app.SECRET_KEY

    # ログ設定
    logging.basicConfig(
        level=getattr(logging, config.app.LOG_LEVEL),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Cloud Storageクライアントの初期化
    bucket = None
    if storage_client:
        try:
            bucket = storage_client.bucket(os.getenv('BUCKET_NAME', 'price-comparison-app-data'))
            app.logger.info("Google Cloud Storage client initialized successfully")
        except Exception as e:
            app.logger.error(f"Failed to initialize Google Cloud Storage: {e}")
            bucket = None
    else:
        app.logger.warning("Google Cloud Storage client not available")

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
        return jsonify({
            'status': 'healthy', 
            'timestamp': datetime.now().isoformat(),
            'storage_available': bucket is not None
        }), 200

    @app.route('/api/status')
    def api_status():
        """APIステータスエンドポイント"""
        return jsonify({
            'app': 'Price Comparison App',
            'version': '1.0.0',
            'environment': os.getenv('APP_ENV', 'production'),
            'storage_available': bucket is not None,
            'timestamp': datetime.now().isoformat()
        }), 200

    @app.route('/scrape-prices', methods=['POST'])
    def scrape_prices():
        """価格スクレイピングエンドポイント（現在は無効化）"""
        return jsonify({
            'error': 'Scraping functionality is currently disabled in App Engine Standard environment',
            'message': 'This feature requires Cloud Run or App Engine Flexible environment'
        }), 503

    @app.route('/set-alert', methods=['POST'])
    def set_alert():
        """アラート設定エンドポイント（現在は無効化）"""
        return jsonify({
            'error': 'Alert functionality is currently disabled in App Engine Standard environment',
            'message': 'This feature requires Cloud Storage access'
        }), 503

    @app.route('/check-prices', methods=['GET'])
    def check_prices():
        """価格チェックエンドポイント（現在は無効化）"""
        return jsonify({
            'error': 'Price checking functionality is currently disabled in App Engine Standard environment',
            'message': 'This feature requires Cloud Storage access'
        }), 503

    @app.route('/api/prices')
    def proxy_prices():
        """価格データプロキシエンドポイント（現在は無効化）"""
        return jsonify({
            'error': 'Price data API is currently disabled in App Engine Standard environment',
            'message': 'This feature requires external API access'
        }), 503

    @app.route("/get_prices")
    def get_prices():
        """価格取得エンドポイント（現在は無効化）"""
        return jsonify({
            'error': 'Price retrieval functionality is currently disabled in App Engine Standard environment',
            'message': 'This feature requires web scraping capabilities'
        }), 503

    return app

# アプリケーションインスタンスを作成
app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
