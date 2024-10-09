from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# 買取ルデアのiPhone 16買取価格ページURL
url_kaitori = 'https://kaitori-rudeya.com/category/detail/183'

# Seleniumを使用して買取価格情報を取得する関数
def get_kaitori_prices(url):
    # Chromeドライバを使用
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    driver.get(url)

    # ページが完全に読み込まれるのを待つ
    driver.implicitly_wait(10)  # 10秒待機

    # 買取価格を取得
    prices = driver.find_elements(By.CSS_SELECTOR, '.td.td2 .td2wrap')

    # 取得した価格情報をリストに格納
    kaitori_prices = [price.text for price in prices if '円' in price.text]

    driver.quit()  # ブラウザを閉じる
    return kaitori_prices

# 買取ルデアの価格取得
iphone16_kaitori_prices = get_kaitori_prices(url_kaitori)

# 結果を出力
print("買取ルデアのiPhone 16の買取価格:")
for price in iphone16_kaitori_prices:
    print(price)
