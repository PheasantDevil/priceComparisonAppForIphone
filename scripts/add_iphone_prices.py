import json
import os

from google.cloud import firestore
from google.oauth2 import service_account


def add_prices_to_firestore():
    # 認証情報の設定
    credentials = service_account.Credentials.from_service_account_file('gcp-key.json')
    
    # Firestoreクライアントの初期化
    db = firestore.Client(credentials=credentials)

    # 公式価格データ
    official_prices = {
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

    # 買取価格データ
    kaitori_prices = {
        "iPhone 17": {
            "256GB": {
                "colors": {
                    "Lavender": 120000,
                    "Sage": 120000,
                    "Black": 120000,
                    "White": 120000,
                    "Mist Blue": 120000
                },
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
                "source": "kaitori-rudea"
            },
            "512GB": {
                "colors": {
                    "Natural Titanium": 210200,
                    "Blue Titanium": 210200,
                    "White Titanium": 210200,
                    "Black Titanium": 210200
                },
                "source": "kaitori-rudea"
            },
            "1TB": {
                "colors": {
                    "Natural Titanium": 243200,
                    "Blue Titanium": 243200,
                    "White Titanium": 243200,
                    "Black Titanium": 243200
                },
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
                "source": "kaitori-rudea"
            },
            "512GB": {
                "colors": {
                    "Natural Titanium": 236200,
                    "Blue Titanium": 236200,
                    "White Titanium": 236200,
                    "Black Titanium": 236200
                },
                "source": "kaitori-rudea"
            },
            "1TB": {
                "colors": {
                    "Natural Titanium": 276200,
                    "Blue Titanium": 276200,
                    "White Titanium": 276200,
                    "Black Titanium": 276200
                },
                "source": "kaitori-rudea"
            },
            "2TB": {
                "colors": {
                    "Natural Titanium": 330200,
                    "Blue Titanium": 330200,
                    "White Titanium": 330200,
                    "Black Titanium": 330200
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
    add_prices_to_firestore() 