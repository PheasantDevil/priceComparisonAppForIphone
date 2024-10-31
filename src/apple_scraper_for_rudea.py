import logging
from playwright.sync_api import sync_playwright
from config import config

logger = logging.getLogger(__name__)

def get_kaitori_prices():
    """買取価格を取得する関数"""
    all_product_details = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(chromium_sandbox=False)
        page = browser.new_page()
        
        try:
            for url in config.scraper.KAITORI_RUDEA_URLS:
                page.goto(url)
                page.wait_for_load_state('networkidle')

                items = page.query_selector_all('.tr')
                product_details = []

                for item in items:
                    try:
                        model_element = item.query_selector('.ttl h2')
                        model_name = model_element.inner_text().strip() if model_element else ""
                        
                        price_element = item.query_selector('.td.td2 .td2wrap')
                        price_text = price_element.inner_text().strip() if price_element else ""

                        if model_name and price_text and '円' in price_text:
                            product_details.append({
                                "model": model_name,
                                "price": price_text
                            })
                    except Exception as e:
                        logger.error(f"データ取得エラー: {str(e)}")
                        continue

                all_product_details.extend(product_details)
            
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
    for price in prices:
        print(f"モデル: {price['model']} | 価格: {price['price']}")
