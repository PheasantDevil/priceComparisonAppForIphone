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
            "iPhone 17": {
                "256GB": {
                    "colors": {
                        "Lavender": 120000,
                        "Sage": 120000,
                        "Black": 120000,
                        "White": 120000,
                        "Mist Blue": 120000
                    },
                    "kaitori_price_min": 120000,
                    "kaitori_price_max": 120000,
                    "source": "kaitori-rudea"
                },
                "512GB": {
                    "colors": {
                        "Lavender": 150000,
                        "Sage": 150000,
                        "Black": 150000,
                        "White": 150000,
                        "Mist Blue": 150000
                    },
                    "kaitori_price_min": 150000,
                    "kaitori_price_max": 150000,
                    "source": "kaitori-rudea"
                }
            },
            "iPhone 17 Air": {
                "256GB": {
                    "colors": {
                        "Light Gold": 146000,
                        "Sage": 146000,
                        "Black": 146000,
                        "White": 146000,
                        "Mist Blue": 146000
                    },
                    "kaitori_price_min": 146000,
                    "kaitori_price_max": 146000,
                    "source": "kaitori-rudea"
                },
                "512GB": {
                    "colors": {
                        "Light Gold": 176000,
                        "Sage": 176000,
                        "Black": 176000,
                        "White": 176000,
                        "Mist Blue": 176000
                    },
                    "kaitori_price_min": 176000,
                    "kaitori_price_max": 176000,
                    "source": "kaitori-rudea"
                },
                "1TB": {
                    "colors": {
                        "Light Gold": 201000,
                        "Sage": 201000,
                        "Black": 201000,
                        "White": 201000,
                        "Mist Blue": 201000
                    },
                    "kaitori_price_min": 201000,
                    "kaitori_price_max": 201000,
                    "source": "kaitori-rudea"
                }
            },
            "iPhone 17 Pro": {
                "256GB": {
                    "colors": {
                        "Natural Titanium": 177200,
                        "Blue Titanium": 177200,
                        "White Titanium": 177200,
                        "Black Titanium": 177200
                    },
                    "kaitori_price_min": 177200,
                    "kaitori_price_max": 177200,
                    "source": "kaitori-rudea"
                },
                "512GB": {
                    "colors": {
                        "Natural Titanium": 210200,
                        "Blue Titanium": 210200,
                        "White Titanium": 210200,
                        "Black Titanium": 210200
                    },
                    "kaitori_price_min": 210200,
                    "kaitori_price_max": 210200,
                    "source": "kaitori-rudea"
                },
                "1TB": {
                    "colors": {
                        "Natural Titanium": 243200,
                        "Blue Titanium": 243200,
                        "White Titanium": 243200,
                        "Black Titanium": 243200
                    },
                    "kaitori_price_min": 243200,
                    "kaitori_price_max": 243200,
                    "source": "kaitori-rudea"
                }
            },
            "iPhone 17 Pro Max": {
                "256GB": {
                    "colors": {
                        "Natural Titanium": 210200,
                        "Blue Titanium": 210200,
                        "White Titanium": 210200,
                        "Black Titanium": 210200
                    },
                    "kaitori_price_min": 210200,
                    "kaitori_price_max": 210200,
                    "source": "kaitori-rudea"
                },
                "512GB": {
                    "colors": {
                        "Natural Titanium": 236200,
                        "Blue Titanium": 236200,
                        "White Titanium": 236200,
                        "Black Titanium": 236200
                    },
                    "kaitori_price_min": 236200,
                    "kaitori_price_max": 236200,
                    "source": "kaitori-rudea"
                },
                "1TB": {
                    "colors": {
                        "Natural Titanium": 276200,
                        "Blue Titanium": 276200,
                        "White Titanium": 276200,
                        "Black Titanium": 276200
                    },
                    "kaitori_price_min": 276200,
                    "kaitori_price_max": 276200,
                    "source": "kaitori-rudea"
                },
                "2TB": {
                    "colors": {
                        "Natural Titanium": 330200,
                        "Blue Titanium": 330200,
                        "White Titanium": 330200,
                        "Black Titanium": 330200
                    },
                    "kaitori_price_min": 330200,
                    "kaitori_price_max": 330200,
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