import logging
from playwright.sync_api import sync_playwright
from config import config

logger = logging.getLogger(__name__)

def get_kaitori_prices():
    """買取価格を取得する関数"""
    all_product_details = {
        'iPhone 16': {},
        'iPhone 16 Pro': {},
        'iPhone 16 Pro Max': {}
    }
    
    with sync_playwright() as p:
        try:
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
                            continue  # 対象外のモデルはスキップ

                        price_element = item.query_selector('.td.td2 .td2wrap')
                        price_text = price_element.inner_text().strip() if price_element else ""

                        if model_name and price_text and '円' in price_text:
                            all_product_details[series][model_name] = price_text
                    except Exception as e:
                        logger.error(f"データ取得エラー: {str(e)}")
                        continue

            return all_product_details
            
        except Exception as e:
            logger.error(f"スクレイピングエラー: {str(e)}")
            raise
            
        finally:
            browser.close()

if __name__ == '__main__':
    # ログ設定
    logging.basicConfig(
        level=getattr(logging, config.app.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 価格取得テスト
    prices = get_kaitori_prices()
    for series, models in prices.items():
        for model, price in models.items():
            print(f"シリーズ: {series} | モデル: {model} | 価格: {price}")
