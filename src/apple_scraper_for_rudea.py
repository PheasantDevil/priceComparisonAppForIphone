from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# 買取ルデアのiPhone 16買取価格ページURL
url_kaitori = 'https://kaitori-rudeya.com/category/detail/183'

def get_kaitori_prices(url):
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    driver.get(url)

    driver.implicitly_wait(10)

    items = driver.find_elements(By.CSS_SELECTOR, '.tr')
    product_details = []
    error_log = []

    for item in items:
        model_name = "不明"
        price_text = "不明"

        # モデル名を取得
        try:
            model_element = item.find_element(By.CSS_SELECTOR, '.ttl h2')
            model_name = model_element.text.strip()
        except Exception as e:
            error_log.append(f"モデル名取得エラー: {e} - 行にモデル名が存在しませんでした。")

        # 買取価格を取得
        try:
            price_element = item.find_element(By.CSS_SELECTOR, '.td.td2 .td2wrap')
            price_text = price_element.text.strip()
        except Exception as e:
            error_log.append(f"買取価格取得エラー: {e} - 行に買取価格が存在しませんでした。")

        if model_name and price_text and '円' in price_text:
            product_details.append({
                "model": model_name,
                "price": price_text
            })

    driver.quit()
    return product_details, error_log

# 買取ルデアの価格取得
iphone16_kaitori_prices, error_log = get_kaitori_prices(url_kaitori)

# 結果を出力
print("買取ルデアのiPhone 16の買取価格:")
for detail in iphone16_kaitori_prices:
    print(f"モデル: {detail['model']} | 買取価格: {detail['price']}")

# エラー情報を表示
if error_log:
    print("\nエラー情報:")
    for error in error_log:
        print(error)
