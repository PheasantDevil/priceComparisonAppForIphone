# Dockerのイメージ名: price-comparison-app:latest

# ベースイメージを指定
FROM python:3.11-slim

# 必要なシステムパッケージとPlaywrightの依存ライブラリをインストール
RUN apt-get update && apt-get install -y \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libatspi2.0-0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libxkbcommon0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Pythonの作業ディレクトリを設定
WORKDIR /app

# プロジェクトのファイルをコピー
COPY . /app

# PythonパッケージとPlaywrightのブラウザをインストール
RUN pip install -r requirements.txt \
    && playwright install

# 環境変数を設定
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/render/.cache/ms-playwright

# アプリケーションを起動
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000"]

