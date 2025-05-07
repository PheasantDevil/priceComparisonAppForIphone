# Dockerのイメージ名: price-comparison-app:latest

# ベースイメージを安定版のPythonに変更
FROM python:3.13-slim

# 必要なシステムパッケージとPlaywrightの依存ライブラリをインストール
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libatspi2.0-0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libxkbcommon0 \
    libgdk-pixbuf2.0-0 \
    libgtk-3-0 \
    libpango-1.0-0 \
    libxshmfence1 \
    libgbm1 \
    libasound2 \
    libcurl4 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリを設定
WORKDIR /app

# 依存関係ファイルを先にコピーしてキャッシュを活用
COPY requirements.txt .

# Pythonパッケージのインストール
RUN pip install --no-cache-dir -r requirements.txt

# Playwrightの環境変数を設定
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/render/.cache/ms-playwright

# Playwrightブラウザのインストール
RUN playwright install chromium

# プロジェクトのファイルをコピー
COPY . .

# アプリケーションを起動
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000", "--workers=3", "--timeout=60"]
