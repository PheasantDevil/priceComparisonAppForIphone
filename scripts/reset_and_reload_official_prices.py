import json

from google.cloud import firestore
from google.oauth2 import service_account


def get_current_official_prices():
    """現在のFirestoreから公式価格データを取得"""
    credentials = service_account.Credentials.from_service_account_file('key.json')
    db = firestore.Client(credentials=credentials)
    
    current_data = {}
    docs = db.collection('official_prices').stream()
    
    for doc in docs:
        data = doc.to_dict()
        series = doc.id
        
        if 'price' in data:
            current_data[series] = data['price']
        else:
            current_data[series] = data
    
    print(f"Retrieved current data for {len(current_data)} series")
    return current_data


def reset_and_reload_official_prices():
    credentials = service_account.Credentials.from_service_account_file('key.json')
    db = firestore.Client(credentials=credentials)

    # 現在のデータを取得
    print("Retrieving current official prices data...")
    current_data = get_current_official_prices()
    
    # データが存在しない場合はダミーデータを使用
    if not current_data:
        print("No current data found, using dummy data...")
        current_data = {
            "iPhone 17": {
                "256GB": {
                    "colors": {
                        "Lavender": 129800,
                        "Sage": 129800,
                        "Black": 129800,
                        "White": 129800,
                        "Mist Blue": 129800
                    }
                },
                "512GB": {
                    "colors": {
                        "Lavender": 164800,
                        "Sage": 164800,
                        "Black": 164800,
                        "White": 164800,
                        "Mist Blue": 164800
                    }
                }
            },
            "iPhone 17 Air": {
                "256GB": {
                    "colors": {
                        "Light Gold": 159800,
                        "Sage": 159800,
                        "Black": 159800,
                        "White": 159800,
                        "Mist Blue": 159800
                    }
                },
                "512GB": {
                    "colors": {
                        "Light Gold": 194800,
                        "Sage": 194800,
                        "Black": 194800,
                        "White": 194800,
                        "Mist Blue": 194800
                    }
                },
                "1TB": {
                    "colors": {
                        "Light Gold": 229800,
                        "Sage": 229800,
                        "Black": 229800,
                        "White": 229800,
                        "Mist Blue": 229800
                    }
                }
            },
            "iPhone 17 Pro": {
                "256GB": {
                    "colors": {
                        "Natural Titanium": 179800,
                        "Blue Titanium": 179800,
                        "White Titanium": 179800,
                        "Black Titanium": 179800
                    }
                },
                "512GB": {
                    "colors": {
                        "Natural Titanium": 214800,
                        "Blue Titanium": 214800,
                        "White Titanium": 214800,
                        "Black Titanium": 214800
                    }
                },
                "1TB": {
                    "colors": {
                        "Natural Titanium": 249800,
                        "Blue Titanium": 249800,
                        "White Titanium": 249800,
                        "Black Titanium": 249800
                    }
                }
            },
            "iPhone 17 Pro Max": {
                "256GB": {
                    "colors": {
                        "Natural Titanium": 194800,
                        "Blue Titanium": 194800,
                        "White Titanium": 194800,
                        "Black Titanium": 194800
                    }
                },
                "512GB": {
                    "colors": {
                        "Natural Titanium": 229800,
                        "Blue Titanium": 229800,
                        "White Titanium": 229800,
                        "Black Titanium": 229800
                    }
                },
                "1TB": {
                    "colors": {
                        "Natural Titanium": 264800,
                        "Blue Titanium": 264800,
                        "White Titanium": 264800,
                        "Black Titanium": 264800
                    }
                },
                "2TB": {
                    "colors": {
                        "Natural Titanium": 329800,
                        "Blue Titanium": 329800,
                        "White Titanium": 329800,
                        "Black Titanium": 329800
                    }
                }
            }
        }

    # 旧データの削除
    docs = db.collection('official_prices').stream()
    for doc in docs:
        doc.reference.delete()
    print("Deleted all existing official_prices documents.")

    # 現在のデータ（またはダミーデータ）の再投入
    for series, data in current_data.items():
        doc_ref = db.collection('official_prices').document(series)
        doc_ref.set({'price': data})
        print(f"Added official prices for {series}")

if __name__ == "__main__":
    reset_and_reload_official_prices() 