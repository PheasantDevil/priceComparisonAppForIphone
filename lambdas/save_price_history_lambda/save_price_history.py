import json
import time
from datetime import datetime, timedelta

import boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('price_history')

def lambda_handler(event, context):
    try:
        # Log the incoming event
        print(f"Processing event: {json.dumps(event)}")
        
        # Get current timestamp
        current_timestamp = int(time.time())
        
        # Calculate expiration time (2 months from now)
        expiration_time = int((datetime.now() + timedelta(days=60)).timestamp())
        
        # Get price data from event
        price_data = event.get('price_data', {})
        
        # Validate price data
        if not price_data:
            print("Warning: No price data found in event")
            return {
                'statusCode': 400,
                'body': json.dumps('No price data provided')
            }
        
        # Save each model's price data
        items_processed = 0
        for model, capacities in price_data.items():
            for capacity, colors in capacities.items():
                for color, price in colors.items():
                    # Validate price
                    try:
                        price = int(price) if isinstance(price, str) else price
                    except ValueError:
                        print(f"Warning: Invalid price value for {model}-{capacity}-{color}: {price}")
                        continue
                        
                    item = {
                        'model': f"{model}-{capacity}-{color}",
                        'timestamp': current_timestamp,
                        'price': price,
                        'expiration_time': expiration_time
                    }
                    
                    table.put_item(Item=item)
                    items_processed += 1
        
        print(f"Successfully processed {items_processed} price items")
        
        return {
            'statusCode': 200,
            'body': json.dumps(f'Price history saved successfully: {items_processed} items processed')
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error saving price history: {str(e)}')
        } 