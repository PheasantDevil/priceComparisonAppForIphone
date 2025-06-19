import json

from google.cloud import firestore
from google.oauth2 import service_account


def get_current_kaitori_prices():
    """現在のFirestoreから買取価格データを取得"""
    credentials = service_account.Credentials.from_service_account_file('key.json')
    db = firestore.Client(credentials=credentials)
    
    current_data = {}
    docs = db.collection('kaitori_prices').stream()
    
    for doc in docs:
        data = doc.to_dict()
        series = data.get('series')
        capacity = data.get('capacity')
        
        if series and capacity:
            if series not in current_data:
                current_data[series] = {}
            
            current_data[series][capacity] = {
                'colors': data.get('colors', {}),
                'kaitori_price_min': data.get('kaitori_price_min', 0),
                'kaitori_price_max': data.get('kaitori_price_max', 0),
                'source': data.get('source', 'kaitori-rudea')
            }
    
    print(f"Retrieved current data for {len(current_data)} series")
    return current_data


def reset_and_reload_kaitori_prices():
    credentials = service_account.Credentials.from_service_account_file('key.json')
    db = firestore.Client(credentials=credentials)

    # 現在のデータを取得
    print("Retrieving current kaitori prices data...")
    current_data = get_current_kaitori_prices()
    
    # データが存在しない場合はダミーデータを使用
    if not current_data:
        print("No current data found, using dummy data...")
        current_data = {
            "iPhone 16": {
                "128GB": {
                    "colors": {
                        "Black": 65000,
                        "White": 65000,
                        "Blue": 65000,
                        "Green": 65000
                    },
                    "kaitori_price_min": 65000,
                    "kaitori_price_max": 65000,
                    "source": "kaitori-rudea"
                },
                "256GB": {
                    "colors": {
                        "Black": 70000,
                        "White": 70000,
                        "Blue": 70000,
                        "Green": 70000
                    },
                    "kaitori_price_min": 70000,
                    "kaitori_price_max": 70000,
                    "source": "kaitori-rudea"
                },
                "512GB": {
                    "colors": {
                        "Black": 80000,
                        "White": 80000,
                        "Blue": 80000,
                        "Green": 80000
                    },
                    "kaitori_price_min": 80000,
                    "kaitori_price_max": 80000,
                    "source": "kaitori-rudea"
                }
            },
            "iPhone 16 Plus": {
                "128GB": {
                    "colors": {
                        "Black": 70000,
                        "White": 70000,
                        "Blue": 70000,
                        "Green": 70000
                    },
                    "kaitori_price_min": 70000,
                    "kaitori_price_max": 70000,
                    "source": "kaitori-rudea"
                },
                "256GB": {
                    "colors": {
                        "Black": 75000,
                        "White": 75000,
                        "Blue": 75000,
                        "Green": 75000
                    },
                    "kaitori_price_min": 75000,
                    "kaitori_price_max": 75000,
                    "source": "kaitori-rudea"
                },
                "512GB": {
                    "colors": {
                        "Black": 85000,
                        "White": 85000,
                        "Blue": 85000,
                        "Green": 85000
                    },
                    "kaitori_price_min": 85000,
                    "kaitori_price_max": 85000,
                    "source": "kaitori-rudea"
                }
            },
            "iPhone 16 Pro": {
                "128GB": {
                    "colors": {
                        "Natural Titanium": 85000,
                        "Blue Titanium": 85000,
                        "White Titanium": 85000,
                        "Black Titanium": 85000
                    },
                    "kaitori_price_min": 85000,
                    "kaitori_price_max": 85000,
                    "source": "kaitori-rudea"
                },
                "256GB": {
                    "colors": {
                        "Natural Titanium": 90000,
                        "Blue Titanium": 90000,
                        "White Titanium": 90000,
                        "Black Titanium": 90000
                    },
                    "kaitori_price_min": 90000,
                    "kaitori_price_max": 90000,
                    "source": "kaitori-rudea"
                },
                "512GB": {
                    "colors": {
                        "Natural Titanium": 100000,
                        "Blue Titanium": 100000,
                        "White Titanium": 100000,
                        "Black Titanium": 100000
                    },
                    "kaitori_price_min": 100000,
                    "kaitori_price_max": 100000,
                    "source": "kaitori-rudea"
                },
                "1TB": {
                    "colors": {
                        "Natural Titanium": 110000,
                        "Blue Titanium": 110000,
                        "White Titanium": 110000,
                        "Black Titanium": 110000
                    },
                    "kaitori_price_min": 110000,
                    "kaitori_price_max": 110000,
                    "source": "kaitori-rudea"
                }
            },
            "iPhone 16 Pro Max": {
                "256GB": {
                    "colors": {
                        "Natural Titanium": 95000,
                        "Blue Titanium": 95000,
                        "White Titanium": 95000,
                        "Black Titanium": 95000
                    },
                    "kaitori_price_min": 95000,
                    "kaitori_price_max": 95000,
                    "source": "kaitori-rudea"
                },
                "512GB": {
                    "colors": {
                        "Natural Titanium": 105000,
                        "Blue Titanium": 105000,
                        "White Titanium": 105000,
                        "Black Titanium": 105000
                    },
                    "kaitori_price_min": 105000,
                    "kaitori_price_max": 105000,
                    "source": "kaitori-rudea"
                },
                "1TB": {
                    "colors": {
                        "Natural Titanium": 115000,
                        "Blue Titanium": 115000,
                        "White Titanium": 115000,
                        "Black Titanium": 115000
                    },
                    "kaitori_price_min": 115000,
                    "kaitori_price_max": 115000,
                    "source": "kaitori-rudea"
                }
            },
            "iPhone 16 e": {
                "128GB": {
                    "colors": {
                        "Black": 55000,
                        "White": 55000
                    },
                    "kaitori_price_min": 55000,
                    "kaitori_price_max": 55000,
                    "source": "kaitori-rudea"
                },
                "256GB": {
                    "colors": {
                        "Black": 60000,
                        "White": 60000
                    },
                    "kaitori_price_min": 60000,
                    "kaitori_price_max": 60000,
                    "source": "kaitori-rudea"
                },
                "512GB": {
                    "colors": {
                        "Black": 70000,
                        "White": 70000
                    },
                    "kaitori_price_min": 70000,
                    "kaitori_price_max": 70000,
                    "source": "kaitori-rudea"
                }
            }
        }

    # 旧データの削除
    docs = db.collection('kaitori_prices').stream()
    for doc in docs:
        doc.reference.delete()
    print("Deleted all existing kaitori_prices documents.")

    # 現在のデータ（またはダミーデータ）の再投入
    for series, capacities in current_data.items():
        for capacity, data in capacities.items():
            doc_ref = db.collection('kaitori_prices').document()
            doc_ref.set({
                'series': series,
                'capacity': capacity,
                'kaitori_price_max': data['kaitori_price_max'],
                'kaitori_price_min': data['kaitori_price_min'],
                'colors': data['colors'],
                'source': data['source']
            })
            print(f"Added kaitori prices for {series} {capacity}")

if __name__ == "__main__":
    reset_and_reload_kaitori_prices() 