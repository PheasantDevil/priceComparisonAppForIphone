from google.cloud import firestore

# Firestoreクライアントの初期化
db = firestore.Client()

# テストデータの準備
official_prices = {
    'iPhone 16': {
        'price': {
            '128GB': 99800,
            '256GB': 109800,
            '512GB': 129800
        }
    },
    'iPhone 16 Pro': {
        'price': {
            '128GB': 129800,
            '256GB': 139800,
            '512GB': 159800,
            '1TB': 179800
        }
    }
}

kaitori_prices = [
    {
        'series': 'iPhone 16',
        'capacity': '128GB',
        'kaitori_price_max': 85000
    },
    {
        'series': 'iPhone 16',
        'capacity': '256GB',
        'kaitori_price_max': 95000
    },
    {
        'series': 'iPhone 16',
        'capacity': '512GB',
        'kaitori_price_max': 115000
    },
    {
        'series': 'iPhone 16 Pro',
        'capacity': '128GB',
        'kaitori_price_max': 115000
    },
    {
        'series': 'iPhone 16 Pro',
        'capacity': '256GB',
        'kaitori_price_max': 125000
    },
    {
        'series': 'iPhone 16 Pro',
        'capacity': '512GB',
        'kaitori_price_max': 145000
    },
    {
        'series': 'iPhone 16 Pro',
        'capacity': '1TB',
        'kaitori_price_max': 165000
    }
]

# データの追加
def seed_data():
    # 公式価格の追加
    for series, data in official_prices.items():
        db.collection('official_prices').document(series).set(data)
        print(f"Added official prices for {series}")

    # 買取価格の追加
    for price in kaitori_prices:
        db.collection('kaitori_prices').add(price)
        print(f"Added kaitori price for {price['series']} {price['capacity']}")

if __name__ == '__main__':
    seed_data() 