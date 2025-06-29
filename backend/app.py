import json
import logging
import os
from datetime import datetime

from flask import Flask, jsonify, render_template, request, send_from_directory


# CORS対応のための関数
def add_cors_headers(response):
    """CORSヘッダーを追加する関数"""
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

# Google Cloud Storageクライアントの初期化
storage_client = None
bucket = None

# Railway環境ではGoogle Cloud Storageはオプション
USE_GOOGLE_CLOUD_STORAGE = os.getenv('USE_GOOGLE_CLOUD_STORAGE', 'false').lower() == 'true'

if USE_GOOGLE_CLOUD_STORAGE:
    try:
        from google.cloud import storage
        from google.oauth2 import service_account

        # 環境変数から認証情報を取得
        credentials_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
        
        if credentials_json:
            try:
                # JSON文字列から認証情報を作成
                credentials_info = json.loads(credentials_json)
                credentials = service_account.Credentials.from_service_account_info(credentials_info)
                storage_client = storage.Client(credentials=credentials)
                print("Google Cloud Storage client initialized with service account")
            except Exception as e:
                print(f"Warning: Could not initialize Google Cloud Storage client with service account: {e}")
                # デフォルトの認証方法を試行
                try:
                    storage_client = storage.Client()
                    print("Google Cloud Storage client initialized with default credentials")
                except Exception as e2:
                    print(f"Warning: Could not initialize Google Cloud Storage client: {e2}")
        else:
            # 環境変数がない場合はデフォルトの認証方法を試行
            try:
                storage_client = storage.Client()
                print("Google Cloud Storage client initialized with default credentials")
            except Exception as e:
                print(f"Warning: Could not initialize Google Cloud Storage client: {e}")
                
    except ImportError as e:
        print(f"Warning: Google Cloud Storage library not available: {e}")
    except Exception as e:
        print(f"Warning: Could not initialize Google Cloud Storage client: {e}")
else:
    print("Google Cloud Storage is disabled for Railway environment")

# 設定クラス
class FallbackConfig:
    class app:
        DEBUG = False
        SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key-for-production')
        LOG_LEVEL = 'INFO'

config = FallbackConfig()

def create_app():
    """
    Creates and configures the Flask application.
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
    global bucket
    if storage_client and USE_GOOGLE_CLOUD_STORAGE:
        try:
            bucket_name = os.getenv('BUCKET_NAME', 'price-comparison-app-data')
            bucket = storage_client.bucket(bucket_name)
            app.logger.info(f"Google Cloud Storage client initialized successfully with bucket: {bucket_name}")
        except Exception as e:
            app.logger.error(f"Failed to initialize Google Cloud Storage bucket: {e}")
            bucket = None
    else:
        app.logger.info("Google Cloud Storage is disabled - using local storage or no storage")

    @app.route("/favicon.ico")
    def favicon():
        """
        Serves the favicon.ico file from the assets directory.
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
        """メインページ - 静的HTMLファイルを配信"""
        try:
            # 現在のディレクトリを確認
            current_dir = os.getcwd()
            templates_path = os.path.join(current_dir, 'templates')
            
            app.logger.info(f"Current directory: {current_dir}")
            app.logger.info(f"Templates path: {templates_path}")
            app.logger.info(f"Templates exists: {os.path.exists(templates_path)}")
            
            if os.path.exists(templates_path):
                app.logger.info(f"Templates contents: {os.listdir(templates_path)}")
            
            return send_from_directory('templates', 'index.html')
        except FileNotFoundError as e:
            app.logger.error(f"index.html not found: {e}")
            # フォールバック: シンプルなHTMLを返す
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Price Comparison App</title>
                <meta charset="utf-8">
            </head>
            <body>
                <h1>Price Comparison App</h1>
                <p>Static files are being generated. Please try again in a moment.</p>
                <p>Current directory: {}</p>
                <p>Templates exists: {}</p>
            </body>
            </html>
            """.format(os.getcwd(), os.path.exists('templates')), 200
        except Exception as e:
            app.logger.error(f"Error serving index: {e}")
            return f"Error: {str(e)}", 500

    @app.route('/<path:filename>')
    def static_files(filename):
        """静的ファイル（CSS、JS、画像など）を配信"""
        try:
            return send_from_directory('templates', filename)
        except FileNotFoundError:
            # ファイルが見つからない場合は404
            return "File not found", 404

    @app.route('/_next/<path:filename>')
    def next_static_files(filename):
        """Next.jsの静的ファイルを配信"""
        try:
            return send_from_directory('templates/_next', filename)
        except FileNotFoundError:
            return "File not found", 404

    @app.route('/health')
    def health_check():
        """ヘルスチェックエンドポイント"""
        return jsonify({
            'status': 'healthy', 
            'timestamp': datetime.now().isoformat(),
            'storage_available': bucket is not None,
            'storage_enabled': USE_GOOGLE_CLOUD_STORAGE,
            'app': 'Price Comparison App',
            'version': '1.0.0',
            'environment': os.getenv('APP_ENV', 'production')
        }), 200

    @app.route('/api/status')
    def api_status():
        """APIステータスエンドポイント"""
        return jsonify({
            'app': 'Price Comparison App',
            'version': '1.0.0',
            'environment': os.getenv('APP_ENV', 'production'),
            'storage_available': bucket is not None,
            'storage_enabled': USE_GOOGLE_CLOUD_STORAGE,
            'timestamp': datetime.now().isoformat()
        }), 200

    @app.route('/scrape-prices', methods=['POST'])
    def scrape_prices():
        """価格スクレイピングエンドポイント（現在は無効化）"""
        return jsonify({
            'error': 'Scraping functionality is currently disabled in Railway environment',
            'message': 'This feature requires additional setup for web scraping'
        }), 503

    @app.route('/set-alert', methods=['POST'])
    def set_alert():
        """アラート設定エンドポイント（現在は無効化）"""
        return jsonify({
            'error': 'Alert functionality is currently disabled in Railway environment',
            'message': 'This feature requires Cloud Storage access'
        }), 503

    @app.route('/check-prices', methods=['GET'])
    def check_prices():
        """価格チェックエンドポイント（現在は無効化）"""
        return jsonify({
            'error': 'Price checking functionality is currently disabled in Railway environment',
            'message': 'This feature requires Cloud Storage access'
        }), 503

    @app.route('/api/prices')
    def proxy_prices():
        """価格データプロキシエンドポイント"""
        series = request.args.get('series', '')
        
        # サンプルデータを返す（実際のデータ取得は無効化）
        sample_data = {
            'iPhone 16': {
                '128GB': {
                    'official_price': 119800,
                    'kaitori_price': 85000,
                    'price_diff': -34800,
                    'rakuten_diff': -25000
                },
                '256GB': {
                    'official_price': 134800,
                    'kaitori_price': 95000,
                    'price_diff': -39800,
                    'rakuten_diff': -30000
                }
            },
            'iPhone 16 Pro': {
                '128GB': {
                    'official_price': 159800,
                    'kaitori_price': 115000,
                    'price_diff': -44800,
                    'rakuten_diff': -35000
                },
                '256GB': {
                    'official_price': 174800,
                    'kaitori_price': 125000,
                    'price_diff': -49800,
                    'rakuten_diff': -40000
                }
            },
            'iPhone 16 Pro Max': {
                '256GB': {
                    'official_price': 199800,
                    'kaitori_price': 145000,
                    'price_diff': -54800,
                    'rakuten_diff': -45000
                },
                '512GB': {
                    'official_price': 224800,
                    'kaitori_price': 165000,
                    'price_diff': -59800,
                    'rakuten_diff': -50000
                }
            },
            'iPhone 16e': {
                '128GB': {
                    'official_price': 99800,
                    'kaitori_price': 70000,
                    'price_diff': -29800,
                    'rakuten_diff': -20000
                },
                '256GB': {
                    'official_price': 114800,
                    'kaitori_price': 80000,
                    'price_diff': -34800,
                    'rakuten_diff': -25000
                }
            }
        }
        
        if series in sample_data:
            response = jsonify({
                'series': series,
                'prices': sample_data[series]
            })
            return add_cors_headers(response)
        else:
            response = jsonify({
                'error': 'Series not found',
                'message': f'Series "{series}" is not available'
            }), 404
            return add_cors_headers(response[0]), response[1]

    @app.route("/get_prices")
    def get_prices():
        """価格取得エンドポイント（現在は無効化）"""
        response = jsonify({
            'error': 'Price retrieval functionality is currently disabled in Railway environment',
            'message': 'This feature requires web scraping capabilities'
        }), 503
        return add_cors_headers(response[0]), response[1]

    return app

# アプリケーションインスタンスを作成
app = create_app()

if __name__ == '__main__':
    # Railway環境での起動設定
    port = int(os.environ.get('PORT', 8080))
    host = os.environ.get('HOST', '0.0.0.0')
    
    print(f"🚀 Starting Flask app on {host}:{port}")
    print(f"📂 Current working directory: {os.getcwd()}")
    print(f"📂 Templates directory exists: {os.path.exists('templates')}")
    if os.path.exists('templates'):
        print(f"📂 Templates contents: {os.listdir('templates')}")
    
    app.run(host=host, port=port, debug=False)
