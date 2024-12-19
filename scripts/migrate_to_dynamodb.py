import json

import boto3

# AWS DynamoDBクライアントの初期化
dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-1')
table = dynamodb.Table('official_prices')

# JSONファイルの読み込み
with open('data/official_prices.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

# DynamoDBにデータを挿入
for series, capacities in data.items():
    for capacity, colors in capacities.items():
        item = {
            'series': series,
            'capacity': capacity,
            'color_prices': colors  # 各カラーの価格情報を保存
        }
        table.put_item(Item=item)
        print(f"Inserted: {series} - {capacity}")

print("データ移行完了！")
