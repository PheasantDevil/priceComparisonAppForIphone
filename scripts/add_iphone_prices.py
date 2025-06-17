import json
import os

from google.cloud import firestore
from google.oauth2 import service_account


def add_prices_to_firestore():
    # 認証情報の設定
    credentials = service_account.Credentials.from_service_account_file('key.json')
    
    # Firestoreクライアントの初期化
    db = firestore.Client(credentials=credentials)

    # 公式価格データ
    official_prices = {
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

    # 買取価格データ
    kaitori_prices = {
        "iPhone 16 Plus": {
            "128GB": {
                "colors": {
                    "Black": 70000,
                    "White": 70000,
                    "Blue": 70000,
                    "Green": 70000
                },
                "source": "kaitori-rudea"
            },
            "256GB": {
                "colors": {
                    "Black": 75000,
                    "White": 75000,
                    "Blue": 75000,
                    "Green": 75000
                },
                "source": "kaitori-rudea"
            },
            "512GB": {
                "colors": {
                    "Black": 85000,
                    "White": 85000,
                    "Blue": 85000,
                    "Green": 85000
                },
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
                "source": "kaitori-rudea"
            },
            "512GB": {
                "colors": {
                    "Natural Titanium": 105000,
                    "Blue Titanium": 105000,
                    "White Titanium": 105000,
                    "Black Titanium": 105000
                },
                "source": "kaitori-rudea"
            },
            "1TB": {
                "colors": {
                    "Natural Titanium": 115000,
                    "Blue Titanium": 115000,
                    "White Titanium": 115000,
                    "Black Titanium": 115000
                },
                "source": "kaitori-rudea"
            }
        },
        "iPhone 16 e": {
            "128GB": {
                "colors": {
                    "Black": 55000,
                    "White": 55000
                },
                "source": "kaitori-rudea"
            },
            "256GB": {
                "colors": {
                    "Black": 60000,
                    "White": 60000
                },
                "source": "kaitori-rudea"
            },
            "512GB": {
                "colors": {
                    "Black": 70000,
                    "White": 70000
                },
                "source": "kaitori-rudea"
            }
        }
    }

    # 公式価格データの追加
    for series, data in official_prices.items():
        doc_ref = db.collection('official_prices').document(series)
        doc_ref.set({'price': data})
        print(f"Added official prices for {series}")

    # 買取価格データの追加
    for series, capacities in kaitori_prices.items():
        for capacity, data in capacities.items():
            doc_ref = db.collection('kaitori_prices').document()
            doc_ref.set({
                'series': series,
                'capacity': capacity,
                'kaitori_price_max': max(data['colors'].values()),
                'kaitori_price_min': min(data['colors'].values()),
                'colors': data['colors'],
                'source': data['source']
            })
            print(f"Added kaitori prices for {series} {capacity}")

if __name__ == "__main__":
    add_prices_to_firestore() 