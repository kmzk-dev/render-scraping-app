# ベースとなるPythonイメージを指定
FROM python:3.10-slim
# システムパッケージリストを更新し、必要なツールをインストール
# --no-install-recommends で推奨パッケージを除きイメージサイズを削減
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      chromium \
      chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリを設定 (コンテナ内の作業場所)
WORKDIR /app

# 必要なPythonライブラリを記述したファイルをコピー
COPY requirements.txt .

# Pythonライブラリをインストール (--no-cache-dirでイメージサイズを少し節約)
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコード（この場合はテストスクリプト）をコピー
# カレントディレクトリ(ローカル)の全ファイルをコンテナのWORKDIR(/app)にコピー
COPY . .
EXPOSE 8000

# コンテナ起動時に実行するコマンド（テスト用スクリプトを実行）
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
