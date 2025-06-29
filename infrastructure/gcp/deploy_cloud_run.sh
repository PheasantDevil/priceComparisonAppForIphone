#!/bin/bash

# 環境変数の設定
PROJECT_ID="price-comparison-app-463007"
SERVICE_NAME="scrape-prices"
REGION="asia-northeast1"
MEMORY="512Mi"
CPU="1"
TIMEOUT="540s"
BUCKET_NAME="price-comparison-app-data"

# Cloud Runのデプロイ
gcloud run deploy $SERVICE_NAME \
  --project $PROJECT_ID \
  --region $REGION \
  --source functions/scrape_prices \
  --memory $MEMORY \
  --cpu $CPU \
  --timeout $TIMEOUT \
  --set-env-vars BUCKET_NAME=$BUCKET_NAME \
  --allow-unauthenticated \
  --port 8080 \
  --clear-base-image

# Cloud Schedulerの設定
gcloud scheduler jobs create http scrape-prices-scheduler \
  --project $PROJECT_ID \
  --location $REGION \
  --schedule "0 10,22 * * *" \
  --uri "https://$REGION-$PROJECT_ID.run.app/$SERVICE_NAME" \
  --http-method POST \
  --time-zone "Asia/Tokyo" \
  --attempt-deadline 540s 