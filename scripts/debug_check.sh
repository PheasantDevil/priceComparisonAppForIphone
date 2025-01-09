read -p "スクリプトを開始しますか？ (yes/no): " response
if [[ $response =~ ^([yY][eE][sS]|[yY])$ ]]
then
    read -p "ログを残しますか？ (yes/no): " log_response
    if [[ $log_response =~ ^([yY][eE][sS]|[yY])$ ]]
    then
        script lambda-deploy.log
    else
        script ex-log.log
    fi
    ls -la artifacts/lambda/
    ls -la artifacts/lambda/function_latest.zip
    # スクリプトに実行権限を付与（初回のみ）
    chmod +x scripts/deploy_lambda.sh

    # デプロイパッケージを作成
    if ./scripts/deploy_lambda.sh; then
        aws lambda update-function-code \
            --function-name get_prices_lambda \
            --zip-file fileb://artifacts/lambda/function_latest
    else
        echo "デプロイパッケージの作成に失敗しました。処理を終了します。"
        exit 1
    fi
else
    echo "スクリプトを開始しない"
fi