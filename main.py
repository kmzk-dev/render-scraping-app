from fastapi import FastAPI, Request, Form, BackgroundTasks, status # BackgroundTasks, status をインポート
from fastapi.responses import HTMLResponse, JSONResponse # JSONResponse を追加
from fastapi.templating import Jinja2Templates
# from pydantic import BaseModel, HttpUrl # 今回のPOSTではFormを使うのでBaseModelは不要かも
import os
import sys
import time
import re
import shutil
from bs4 import BeautifulSoup

# --- functionディレクトリから自作関数をインポート ---
try:
    from function.scraper import get_html_source, get_title, get_img_uri_list
    from function.downloader import download_images
    from function.converter import convert_webp_to_png, create_pdf_from_images
except ImportError as e:
    print(f"Error importing function modules: {e}", file=sys.stderr)

# --- FastAPI アプリケーションインスタンスとテンプレート初期化 ---
app = FastAPI(title="Simple URL Input Form")
templates = Jinja2Templates(directory="templates")

def background_task(target_url: str):
    # 1. HTML取得
    try:
        print("[BG Task 1 Fetching HTML source...")
        html_content = get_html_source(target_url)
        soup = BeautifulSoup(html_content, 'html.parser')
        page_title = get_title(soup)
        img_list = get_img_uri_list(soup)
        print(f"  Title: {page_title}, Images Found: {len(img_list)}")
        if not img_list:
            print("No images found. Task finished.")
            return
    except Exception as e:
        # 全体的なエラーキャッチ (ハンドリング最小限)
        print(f"Error during BG Task1: {e}", file=sys.stderr)
    finally:
        print(f"--- BG Task 1 Finished")
    # 2. 一時ディレクトリの作成
    try:
        print("[BG Task 2 Create temporary directories...")
        timestamp = str(int(time.time()))
        temp_filename = "temp" + timestamp + "img"
        
        output_base_dir = os.path.join("output_data") # Docker環境での出力先ディレクトリ
        os.makedirs(output_base_dir, exist_ok=True) # 出力先ディレクトリを作成
        
        parent_directory = os.path.join(output_base_dir,temp_filename) # 親ディレクトリを作成
        save_directory = os.path.join(parent_directory, "downloaded") # 子ディレクトリを作成
        converted_directory = os.path.join(parent_directory, "converted") # 子ディレクトリを作成
        pdf_directory = os.path.join(parent_directory, "pdf") # 子ディレクトリを作成
        os.makedirs(parent_directory, exist_ok=True) # 親ディレクトリを作成
        os.makedirs(save_directory, exist_ok=True) # 子ディレクトリを作成
        os.makedirs(converted_directory, exist_ok=True) # 子ディレクトリを作成
        os.makedirs(pdf_directory, exist_ok=True) # 子ディレクトリを作成
        print(f"  Temporary directories created: {parent_directory}")
    except Exception as e:
        # 全体的なエラーキャッチ (ハンドリング最小限)
        print(f"Error during BG Task2: {e}", file=sys.stderr)
    finally:
        print(f"--- BG Task 2 Finished")
    # 3. 画像ダウンロード
    try:
        print("[BG Task 3 Downloading images...")
        download_images(img_list, save_directory, temp_filename, ".webp", 0.25)
    except Exception as e:
        print(f"Error during BG Task3: {e}", file=sys.stderr)
    finally:
        print(f"--- BG Task 3 Finished")
    #4. 画像変換
    try:
        print("[BG Task 4 Converting images...")
        convert_webp_to_png(save_directory, converted_directory)
    except Exception as e:
        print(f"Error during BG Task4: {e}", file=sys.stderr)
    finally:
        print(f"--- BG Task 4 Finished")
    # 5. PDF作成
    try:
        print("[BG Task 5 Creating PDF...")
        filename_true = re.sub(r'[\\/:*?"<>|]', '', page_title) # ファイル名に使えない文字を除去
        create_pdf_from_images(converted_directory, pdf_directory, filename_true)
    except Exception as e:
        print(f"Error during BG Task5: {e}", file=sys.stderr)
    finally:
        print(f"--- BG Task 5 Finished")
    # 6. 一時ディレクトリの削除
    try:
        print("[BG Task 6 Cleaning up temporary directories...")
        shutil.rmtree(save_directory) # 一時ディレクトリを削除
        shutil.rmtree(converted_directory) # 一時ディレクトリを削除
    except Exception as e:
        print(f"Error during BG Task6: {e}", file=sys.stderr)
    finally:
        print(f"--- BG Task 6 Finished")
    


# フォームを表示するエンドポイント:ルート
@app.get("/", response_class=HTMLResponse)
async def read_form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# フォームデータを受け取りバックグラウンドタスクを開始するエンドポイント
@app.post("/submit-url/", status_code=status.HTTP_202_ACCEPTED)
async def accept_url_and_start_processing(
    background_tasks: BackgroundTasks, # BackgroundTasks を最初に書くのが一般的
    url: str = Form(...)              # Formデータを受け取る
):

    # process_url_and_generate_pdf 関数をバックグラウンドタスクとして登録
    print(f"Received URL [{url}] via POST request. Adding to background tasks.")
    background_tasks.add_task(background_task, url)

    # 処理が受け付けられたことを示すJSONレスポンスを即座に返す
    return {"message": "Request accepted. Processing started in background.", "submitted_url": url}
