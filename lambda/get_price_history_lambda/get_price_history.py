import json
from datetime import datetime, timedelta

import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('price_history')

def lambda_handler(event, context):
    try:
        # Get query parameters
        query_params = event.get('queryStringParameters', {})
        model = query_params.get('model')
        days = int(query_params.get('days', 30))  # Default to 30 days
        
        # Calculate timestamp for the start date
        start_timestamp = int((datetime.now() - timedelta(days=days)).timestamp())
        
        # Query DynamoDB
        response = table.query(
            KeyConditionExpression=Key('model').eq(model) & Key('timestamp').gte(start_timestamp),
            IndexName='TimestampIndex'
        )
        
        # Format response data
        items = response.get('Items', [])
        formatted_data = []
        
        for item in items:
            formatted_data.append({
                'timestamp': item['timestamp'],
                'price': item['price']
            })
        
        # Sort by timestamp
        formatted_data.sort(key=lambda x: x['timestamp'])
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Credentials': True
            },
            'body': json.dumps(formatted_data)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Credentials': True
            },
            'body': json.dumps(f'Error retrieving price history: {str(e)}')
        } 