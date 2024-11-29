# ベースイメージ
FROM python:3.11-slim

# 必要な依存ライブラリをインストール
RUN apt-get update && apt-get install -y \
    gstreamer1.0-gl \
    gstreamer1.0-libav \
    libavif15 \
    libenchant-2-2 \
    libsecret-1-dev \
    libmanette-0.2-dev \
    libgles2-mesa \
    && rm -rf /var/lib/apt/lists/*

# Python環境のセットアップ
WORKDIR /app
COPY . /app
RUN pip install -r requirements.txt && playwright install

# アプリケーションのエントリーポイント
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000"]
