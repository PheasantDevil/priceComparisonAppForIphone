import logging

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

from config import config

logger = logging.getLogger(__name__)

def get_kaitori_prices():
    """買取価格を取得する関数"""
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    
    try:
        driver.get(config.scraper.KAITORI_RUDEA_URL)
        driver.implicitly_wait(config.scraper.REQUEST_TIMEOUT)

        items = driver.find_elements(By.CSS_SELECTOR, '.tr')
        product_details = []

        for item in items:
            try:
                model_element = item.find_element(By.CSS_SELECTOR, '.ttl h2')
                model_name = model_element.text.strip()
                
                price_element = item.find_element(By.CSS_SELECTOR, '.td.td2 .td2wrap')
                price_text = price_element.text.strip()

                if model_name and price_text and '円' in price_text:
                    product_details.append({
                        "model": model_name,
                        "price": price_text
                    })
            except Exception as e:
                logger.error(f"データ取得エラー: {str(e)}")
                continue

        return product_details
        
    except Exception as e:
        logger.error(f"スクレイピングエラー: {str(e)}")
        raise
        
    finally:
        driver.quit()

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