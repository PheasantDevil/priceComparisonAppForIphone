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
            "iPhone 16": {
                "128GB": {
                    "colors": {
                        "Black": 124800,
                        "White": 124800,
                        "Blue": 124800,
                        "Green": 124800
                    }
                },
                "256GB": {
                    "colors": {
                        "Black": 139800,
                        "White": 139800,
                        "Blue": 139800,
                        "Green": 139800
                    }
                },
                "512GB": {
                    "colors": {
                        "Black": 169800,
                        "White": 169800,
                        "Blue": 169800,
                        "Green": 169800
                    }
                }
            },
            "iPhone 16 Plus": {
                "128GB": {
                    "colors": {
                        "Black": 139800,
                        "White": 139800,
                        "Blue": 139800,
                        "Green": 139800
                    }
                },
                "256GB": {
                    "colors": {
                        "Black": 154800,
                        "White": 154800,
                        "Blue": 154800,
                        "Green": 154800
                    }
                },
                "512GB": {
                    "colors": {
                        "Black": 184800,
                        "White": 184800,
                        "Blue": 184800,
                        "Green": 184800
                    }
                }
            },
            "iPhone 16 Pro": {
                "128GB": {
                    "colors": {
                        "Natural Titanium": 159800,
                        "Blue Titanium": 159800,
                        "White Titanium": 159800,
                        "Black Titanium": 159800
                    }
                },
                "256GB": {
                    "colors": {
                        "Natural Titanium": 174800,
                        "Blue Titanium": 174800,
                        "White Titanium": 174800,
                        "Black Titanium": 174800
                    }
                },
                "512GB": {
                    "colors": {
                        "Natural Titanium": 204800,
                        "Blue Titanium": 204800,
                        "White Titanium": 204800,
                        "Black Titanium": 204800
                    }
                },
                "1TB": {
                    "colors": {
                        "Natural Titanium": 234800,
                        "Blue Titanium": 234800,
                        "White Titanium": 234800,
                        "Black Titanium": 234800
                    }
                }
            },
            "iPhone 16 Pro Max": {
                "256GB": {
                    "colors": {
                        "Natural Titanium": 189800,
                        "Blue Titanium": 189800,
                        "White Titanium": 189800,
                        "Black Titanium": 189800
                    }
                },
                "512GB": {
                    "colors": {
                        "Natural Titanium": 219800,
                        "Blue Titanium": 219800,
                        "White Titanium": 219800,
                        "Black Titanium": 219800
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
            "iPhone 16 e": {
                "128GB": {
                    "colors": {
                        "Black": 99800,
                        "White": 99800
                    }
                },
                "256GB": {
                    "colors": {
                        "Black": 114800,
                        "White": 114800
                    }
                },
                "512GB": {
                    "colors": {
                        "Black": 144800,
                        "White": 144800
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