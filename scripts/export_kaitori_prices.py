import json

from google.cloud import firestore
from google.oauth2 import service_account


def export_kaitori_prices():
    credentials = service_account.Credentials.from_service_account_file('key.json')
    db = firestore.Client(credentials=credentials)

    docs = db.collection('kaitori_prices').stream()
    all_data = [doc.to_dict() for doc in docs]

    # ファイルに保存
    with open('kaitori_prices_export.json', 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    print(f"Exported {len(all_data)} documents to kaitori_prices_export.json")

    # 内容を標準出力にも表示
    for item in all_data:
        print(json.dumps(item, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    export_kaitori_prices() 