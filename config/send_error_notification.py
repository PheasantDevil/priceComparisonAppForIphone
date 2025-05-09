#!/usr/bin/env python3
import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict

import yaml
from linebot import LineBotApi
from linebot.exceptions import LineBotApiError
from linebot.models import TextSendMessage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load config: {str(e)}")
        raise

def create_error_message(error_type: str, error_message: str) -> str:
    """Create formatted error message."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    request_id = os.environ.get('AWS_REQUEST_ID', 'unknown')
    return f"""
🚨 Error Alert 🚨
Type: {error_type}
Time: {timestamp}
Request ID: {request_id}
Message: {error_message}
"""

def send_notification(config: Dict[str, Any], message: str) -> None:
    """Send notification using LINE API."""
    try:
        # 環境変数からLINEチャネルアクセストークンを取得
        channel_access_token = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
        if not channel_access_token:
            logger.error("LINE_CHANNEL_ACCESS_TOKEN environment variable is not set")
            raise ValueError("LINE_CHANNEL_ACCESS_TOKEN is required")

        line_bot_api = LineBotApi(channel_access_token)
        line_bot_api.broadcast(TextSendMessage(text=message))
        logger.info(f"Notification sent successfully for request ID: {os.environ.get('AWS_REQUEST_ID', 'unknown')}")
    except LineBotApiError as e:
        logger.error(f"LINE API error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise

def main():
    """Main function to handle error notifications."""
    try:
        if len(sys.argv) != 3:
            logger.error("Invalid number of arguments")
            logger.error("Usage: python send_error_notification.py <error_type> <error_message>")
            sys.exit(1)

        error_type = sys.argv[1]
        error_message = sys.argv[2]

        # Load configuration
        config_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(config_dir, 'config.testing.yaml')
        config = load_config(config_path)

        # Create and send error message
        message = create_error_message(error_type, error_message)
        send_notification(config, message)

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main() 