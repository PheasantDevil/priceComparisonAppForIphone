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
        if not model:
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Credentials': True
                },
                'body': json.dumps('Missing required parameter: model')
            }
        
        # Calculate date range (2 weeks before and after)
        today = datetime.now()
        start_date = (today - timedelta(days=14)).strftime('%Y-%m-%d')
        end_date = (today + timedelta(days=14)).strftime('%Y-%m-%d')
        
        # Query DynamoDB using DateIndex
        response = table.query(
            IndexName='DateIndex',
            KeyConditionExpression=Key('date').between(start_date, end_date) & Key('model').eq(model)
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