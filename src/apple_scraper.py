import requests
from bs4 import BeautifulSoup

# iPhone 16, iPhone 16 Plusの購入ページURL
url_iphone16 = 'https://www.apple.com/jp/shop/buy-iphone/iphone-16'
# iPhone 16 Pro, iPhone 16 Pro Maxの購入ページURL
url_iphone16_pro = 'https://www.apple.com/jp/shop/buy-iphone/iphone-16-pro'

# ページから価格情報を取得する関数
def get_prices(url):
    # ページを取得
    response = requests.get(url)
    
    # レスポンスの内容を確認
    print(response.text)  # ここでHTMLの内容を表示
    
    # BeautifulSoupでHTML解析
    soup = BeautifulSoup(response.text, 'html.parser')

    # 価格情報を取得するためのセレクタ
    prices = soup.select('span.price-point.price-point-fullPrice > span.nowrap')

    # 取得した価格情報をリストに格納
    price_list = [price.get_text() for price in prices]
    return price_list

# iPhone 16シリーズの価格取得
print("iPhone 16シリーズの価格:")
iphone16_prices = get_prices(url_iphone16)
for price in iphone16_prices:
    print(price)

# iPhone 16 Proシリーズの価格取得
print("\niPhone 16 Proシリーズの価格:")
iphone16_pro_prices = get_prices(url_iphone16_pro)
for price in iphone16_pro_prices:
    print(price)
