from flask import Flask, render_template
from selenium import webdriver
from selenium.webdriver.chrome.options import Options  # 追加
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

app = Flask(__name__)

# スクレイピング関数の定義
def get_kaitori_prices(url):
    # Chromeのオプションにヘッドレスモードを追加
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # ヘッドレスモードを有効化
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)  # オプションを追加

    driver.get(url)
    driver.implicitly_wait(10)

    items = driver.find_elements(By.CSS_SELECTOR, '.tr')
    product_details = []

    for item in items:
        model_name = "不明"
        price_text = "不明"

        try:
            model_element = item.find_element(By.CSS_SELECTOR, '.ttl h2')
            model_name = model_element.text.strip()
        except Exception as e:
            model_name = "エラー: モデル名取得失敗"

        try:
            price_element = item.find_element(By.CSS_SELECTOR, '.td.td2 .td2wrap')
            price_text = price_element.text.strip()
        except Exception as e:
            price_text = "エラー: 買取価格取得失敗"

        if model_name and price_text and '円' in price_text:
            product_details.append({
                "model": model_name,
                "price": price_text
            })

    driver.quit()
    return product_details

# ルートページでスクレイピングデータを取得し表示する
@app.route('/')
def home():
    url_kaitori = 'https://kaitori-rudeya.com/category/detail/183'
    iphone_prices = get_kaitori_prices(url_kaitori)
    return render_template('index.html', iphone_prices=iphone_prices)

if __name__ == '__main__':
    app.run(debug=True)
