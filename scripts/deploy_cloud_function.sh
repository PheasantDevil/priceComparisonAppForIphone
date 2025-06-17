#!/bin/bash

# 環境変数の設定
PROJECT_ID="price-comparison-app-463007"
FUNCTION_NAME="scrape-prices"
REGION="asia-northeast1"
MEMORY="512MB"
TIMEOUT="540s"
BUCKET_NAME="price-comparison-app-data"

# Cloud Functionのデプロイ
gcloud functions deploy $FUNCTION_NAME \
  --project $PROJECT_ID \
  --region $REGION \
  --memory $MEMORY \
  --timeout $TIMEOUT \
  --trigger-http \
  --entry-point scrape_prices \
  --source functions/scrape_prices \
  --set-env-vars BUCKET_NAME=$BUCKET_NAME \
  --allow-unauthenticated \
  --runtime python311 \
  --use-dockerfile

# Cloud Schedulerの設定
gcloud scheduler jobs create http scrape-prices-scheduler \
  --project $PROJECT_ID \
  --location $REGION \
  --schedule "0 10,22 * * *" \
  --uri "https://$REGION-$PROJECT_ID.cloudfunctions.net/$FUNCTION_NAME" \
  --http-method POST \
  --time-zone "Asia/Tokyo" \
  --attempt-deadline 540s 