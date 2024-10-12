from flask import Flask, jsonify, render_template
from playwright.sync_api import sync_playwright

app = Flask(__name__)

# スクレイピング関数の定義
def get_kaitori_prices(url):
    product_details = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        page.wait_for_selector('.tr')  # 適切なセレクタを待つ

        items = page.query_selector_all('.tr')

        for item in items:
            model_name = "不明"
            price_text = "不明"

            try:
                model_element = item.query_selector('.ttl h2')
                model_name = model_element.inner_text().strip()
            except Exception as e:
                model_name = "エラー: モデル名取得失敗"

            try:
                price_element = item.query_selector('.td.td2 .td2wrap')
                price_text = price_element.inner_text().strip()
            except Exception as e:
                price_text = "エラー: 買取価格取得失敗"

            if model_name and price_text and '円' in price_text:
                product_details.append({
                    "model": model_name,
                    "price": price_text
                })

        browser.close()
    return product_details

# ルートページ（HTML表示用）
@app.route('/')
def home():
    return render_template('index.html')

# データ取得用APIエンドポイント
@app.route('/get_prices')
def get_prices():
    url_kaitori = 'https://kaitori-rudeya.com/category/detail/183'
    iphone_prices = get_kaitori_prices(url_kaitori)
    return jsonify(iphone_prices)

if __name__ == '__main__':
    app.run(debug=True)
