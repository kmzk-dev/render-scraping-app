import requests
import os
import time
import sys # エラーメッセージ出力用にインポート

def download_images(img_uri_list, save_directory, file_name, extension=".webp", sleep_time=0.25):
    """
    画像URIのリストから画像をダウンロードし、指定されたディレクトリに保存する。

    Args:
        img_uri_list (list): ダウンロードしたい画像のURI(文字列)が含まれたリスト。
        save_directory (str): 画像を保存するディレクトリのパス。
        file_prefix (str): 保存するファイル名の接頭辞（例: 'page_title_'）。
        extension (str, optional): 保存するファイルの拡張子（ドット込み）。デフォルトは ".webp"。
        sleep_time (float, optional): 各ダウンロード後に待機する秒数。デフォルトは 0.25秒。
    """
    print(f"\n--- Starting Image Download ---")
    if not img_uri_list:
        print("No image URIs provided. Skipping download.")
        return
    if not extension.startswith('.'):
        print("Extension should start with a dot (e.g., '.jpg').")
        return

    print(f"Attempting to download {len(img_uri_list)} images...")
    for i, img_uri in enumerate(img_uri_list):
        file_number = i + 1
        file_path = os.path.join(save_directory, f"{file_name}{file_number}{extension}")
        try:
            response = requests.get(
                img_uri,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                },
                timeout=15)

            # ステータスコードが4xxか5xxの場合は例外を発生させる
            response.raise_for_status()

            # レスポンスの内容をバイナリモード('wb')でファイルに書き込む
            with open(file_path, 'wb') as file:
                file.write(response.content)
        except Exception as e:
            print(f"  An unexpected error occurred for {img_uri}: {e}", file=sys.stderr)
            break  # エラーが発生した場合はループを終了

        time.sleep(sleep_time)
    print(f"downloaded")

    
    