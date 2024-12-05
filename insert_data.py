import json

import psycopg2

# データベース接続
conn = psycopg2.connect(
    host="dpg-ct8or1a3esus7384jdbg-a.oregon-postgres.render.com",
    database="official_prices_db_gop6",
    user="official_prices_db_gop6_user",
    password="ngVU5yXdsM8AMyt0Jy2FdC2fOtfL9Rc0"
)
cursor = conn.cursor()

# JSONデータの読み込み
with open('data/official_prices.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

# データ挿入のためのSQL文
for product, capacities in data.items():
    for capacity, models in capacities.items():
        for model, price in models.items():
            # 価格を挿入する
            cursor.execute("""
                INSERT INTO official_prices (product_name, capacity, color, price)
                VALUES (%s, %s, %s, %s)
            """, (product, capacity, model, price))

# 変更を確定
conn.commit()

# 終了処理
cursor.close()
conn.close()

print("データ挿入完了！")
