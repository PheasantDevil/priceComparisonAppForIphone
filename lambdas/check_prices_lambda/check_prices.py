import json
import os
from datetime import datetime

import boto3
import requests


def lambda_handler(event, context):
    try:
        # Get environment variables
        dynamodb_table = os.environ.get('DYNAMODB_TABLE')
        environment = os.environ.get('ENVIRONMENT')
        line_notify_token = os.environ.get('LINE_NOTIFY_TOKEN')
        
        # Initialize AWS clients
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(dynamodb_table)
        
        # Get current prices
        response = table.scan()
        current_prices = response.get('Items', [])
        
        # Get official prices
        official_table = dynamodb.Table('official_prices')
        official_response = official_table.scan()
        official_prices = official_response.get('Items', [])
        
        # Compare prices
        price_changes = []
        for current_price in current_prices:
            model = current_price.get('model')
            current_price_value = current_price.get('price', 0)
            
            # Find matching official price
            official_price = next(
                (p for p in official_prices if p.get('model') == model),
                None
            )
            
            if official_price:
                official_price_value = official_price.get('price', 0)
                if current_price_value != official_price_value:
                    price_changes.append({
                        'model': model,
                        'current_price': current_price_value,
                        'official_price': official_price_value,
                        'difference': current_price_value - official_price_value
                    })
        
        # Send notification if there are price changes
        if price_changes and line_notify_token:
            message = f"Price changes detected:\n"
            for change in price_changes:
                message += f"Model: {change['model']}\n"
                message += f"Current Price: {change['current_price']}\n"
                message += f"Official Price: {change['official_price']}\n"
                message += f"Difference: {change['difference']}\n\n"
            
            # Send LINE notification
            headers = {
                'Authorization': f'Bearer {line_notify_token}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            data = {
                'message': message
            }
            requests.post('https://notify-api.line.me/api/notify', headers=headers, data=data)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Price check completed',
                'environment': environment,
                'price_changes': price_changes
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Price check failed',
                'error': str(e)
            })
        } 