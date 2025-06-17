#!/bin/bash

# 環境変数の設定
PROJECT_ID="your-project-id"
FUNCTION_NAME="scrape-prices"
REGION="asia-northeast1"
RUNTIME="python311"
MEMORY="512MB"
TIMEOUT="540s"
BUCKET_NAME="your-bucket-name"

# Cloud Functionのデプロイ
gcloud functions deploy $FUNCTION_NAME \
  --project $PROJECT_ID \
  --region $REGION \
  --runtime $RUNTIME \
  --memory $MEMORY \
  --timeout $TIMEOUT \
  --trigger-http \
  --entry-point scrape_prices \
  --source functions/scrape_prices \
  --set-env-vars BUCKET_NAME=$BUCKET_NAME \
  --allow-unauthenticated

# Cloud Schedulerの設定
gcloud scheduler jobs create http scrape-prices-scheduler \
  --project $PROJECT_ID \
  --schedule "0 10,22 * * *" \
  --uri "https://$REGION-$PROJECT_ID.cloudfunctions.net/$FUNCTION_NAME" \
  --http-method POST \
  --time-zone "Asia/Tokyo" \
  --attempt-deadline 540s 