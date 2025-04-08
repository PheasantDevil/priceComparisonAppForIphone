import json
import time
from datetime import datetime, timedelta

import boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('price_history')

def lambda_handler(event, context):
    try:
        # Get current timestamp
        current_timestamp = int(time.time())
        
        # Calculate expiration time (2 months from now)
        expiration_time = int((datetime.now() + timedelta(days=60)).timestamp())
        
        # Get price data from event
        price_data = event.get('price_data', {})
        
        # Save each model's price data
        for model, capacities in price_data.items():
            for capacity, colors in capacities.items():
                for color, price in colors.items():
                    item = {
                        'model': f"{model}-{capacity}-{color}",
                        'timestamp': current_timestamp,
                        'price': price,
                        'expiration_time': expiration_time
                    }
                    
                    table.put_item(Item=item)
        
        return {
            'statusCode': 200,
            'body': json.dumps('Price history saved successfully')
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error saving price history: {str(e)}')
        } 