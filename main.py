import logging
import sys # sysも必要に応じて残す

# ロギングの基本設定 (アプリケーション起動時に1回だけ行う)
# INFOレベル以上のログを出力、フォーマットを指定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s',
    stream=sys.stdout # Renderのログは標準出力へ出すのが一般的
)

import uvicorn
from fastapi import FastAPI, Request, Form, BackgroundTasks, status # BackgroundTasks, status をインポート
from fastapi.responses import HTMLResponse, JSONResponse,RedirectResponse # JSONResponse を追加
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles # ★ これを追加 ★
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
    logging.info(f"Error importing function modules: {e}", file=sys.stderr)

# --- FastAPI アプリケーションインスタンスとテンプレート初期化 ---
app = FastAPI(title="Simple URL Input Form")
templates = Jinja2Templates(directory="templates")

# --- ★ 静的ファイル配信設定を追加 ★ ---
# ローカルの "archives" ディレクトリを準備 (なければ作成)
# このパスはローカル実行時とDocker実行時で挙動が同じになるように相対パス推奨
local_archives_dir = "archives"
try:
    os.makedirs(local_archives_dir, exist_ok=True)
    # "archives" ディレクトリの中身を "/static-archives" というURLパスで配信するようマウント
    app.mount("/static-archives", StaticFiles(directory=local_archives_dir), name="static_archives")
    logging.info(f"Mounted static directory '{local_archives_dir}' to '/static-archives'")
except Exception as e:
    logging.error(f"Failed to mount static directory '{local_archives_dir}': {e}")
# ----------------------------------

def background_task(target_url: str):
    # 1. HTML取得
    try:
        logging.info("[BG Task 1 Fetching HTML source...")
        html_content = get_html_source(target_url)
        soup = BeautifulSoup(html_content, 'html.parser')
        page_title = get_title(soup)
        img_list = get_img_uri_list(soup)
        logging.info(f"  Title: {page_title}, Images Found: {len(img_list)}")
        if not img_list:
            logging.info("No images found. Task finished.")
            return
    except Exception as e:
        # 全体的なエラーキャッチ (ハンドリング最小限)
        logging.info(f"Error during BG Task1: {e}", file=sys.stderr)
    finally:
        logging.info(f"--- BG Task 1 Finished")
    # 2. 一時ディレクトリの作成
    try:
        logging.info("[BG Task 2 Create temporary directories...")
        timestamp = str(int(time.time()))
        temp_filename = "temp" + timestamp + "img"
        
        output_base_dir = os.path.join("output_data") # Docker環境での出力先ディレクトリ
        os.makedirs(output_base_dir, exist_ok=True) # 出力先ディレクトリを作成
        
        parent_directory = os.path.join(output_base_dir,temp_filename) # 親ディレクトリを作成
        save_directory = os.path.join(parent_directory, "downloaded") # 子ディレクトリを作成
        converted_directory = os.path.join(parent_directory, "converted") # 子ディレクトリを作成
        pdf_directory = os.path.join("archives") # 子ディレクトリを作成
        os.makedirs(parent_directory, exist_ok=True) # 親ディレクトリを作成
        os.makedirs(save_directory, exist_ok=True) # 子ディレクトリを作成
        os.makedirs(converted_directory, exist_ok=True) # 子ディレクトリを作成
#        os.makedirs(pdf_directory, exist_ok=True) # 子ディレクトリを作成
        logging.info(f"  Temporary directories created: {parent_directory}")
    except Exception as e:
        # 全体的なエラーキャッチ (ハンドリング最小限)
        logging.info(f"Error during BG Task2: {e}", file=sys.stderr)
    finally:
        logging.info(f"--- BG Task 2 Finished")
    # 3. 画像ダウンロード
    try:
        logging.info("[BG Task 3 Downloading images...")
        download_images(img_list, save_directory, temp_filename, ".webp", 0.25)
    except Exception as e:
        logging.info(f"Error during BG Task3: {e}", file=sys.stderr)
    finally:
        logging.info(f"--- BG Task 3 Finished")
    #4. 画像変換
    try:
        logging.info("[BG Task 4 Converting images...")
        convert_webp_to_png(save_directory, converted_directory)
    except Exception as e:
        logging.info(f"Error during BG Task4: {e}", file=sys.stderr)
    finally:
        logging.info(f"--- BG Task 4 Finished")
    # 5. PDF作成
    try:
        logging.info("[BG Task 5 Creating PDF...")
        filename_true = re.sub(r'[\\/:*?"<>|]', '', page_title) # ファイル名に使えない文字を除去
        create_pdf_from_images(converted_directory, pdf_directory, filename_true)
    except Exception as e:
        logging.info(f"Error during BG Task5: {e}", file=sys.stderr)
    finally:
        logging.info(f"--- BG Task 5 Finished")
    # 6. 一時ディレクトリの削除
    try:
        logging.info("[BG Task 6 Cleaning up temporary directories...")
        shutil.rmtree(save_directory) # 一時ディレクトリを削除
        shutil.rmtree(converted_directory) # 一時ディレクトリを削除
    except Exception as e:
        logging.info(f"Error during BG Task6: {e}", file=sys.stderr)
    finally:
        logging.info(f"--- BG Task 6 Finished")
    

# フォームを表示するエンドポイント:ルート
@app.get("/", response_class=HTMLResponse)
async def read_form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# フォームデータを受け取りバックグラウンドタスクを開始するエンドポイント
@app.post("/submit-url/")
async def accept_url_and_start_processing(
    background_tasks: BackgroundTasks, # BackgroundTasks を最初に書くのが一般的
    url: str = Form(...)              # Formデータを受け取る
):

    """
    フォームからURLを受け取り、バックグラウンドタスクを開始した後、
    すぐに /archives/ ページへリダイレクトする。
    """
    logging.info(f"Received URL [{url}] via POST request. Adding to background tasks.")
    background_tasks.add_task(background_task, url)

    # ★ JSONではなく、リダイレクト応答を返すように変更 ★
    #   status_code=303 See Other は、POSTリクエスト後に
    #   別のページ(結果表示など)にリダイレクトする場合に推奨されるステータスコード
    logging.info("Redirecting client to /archives/ page.")
    return RedirectResponse(url="/archives/", status_code=status.HTTP_303_SEE_OTHER)

# --- ★ PDF一覧表示エンドポイントを新規追加 ★ ---
@app.get("/archives/", response_class=HTMLResponse)
async def show_archives(request: Request):
    """
    ローカルの 'archives' ディレクトリを読み取り、
    PDFファイルの一覧とダウンロードリンクを含むHTMLを返す。
    """
    pdf_dir = "archives" # ローカル実行時の相対パス
    pdf_files_info = []
    error_message = None
    logging.info(f"Access to /archives/ endpoint. Reading directory: {pdf_dir}")

    try:
        # archives ディレクトリが存在するか確認
        if os.path.isdir(pdf_dir):
            # ディレクトリ内のファイルを取得し、'.pdf'で終わるものだけを抽出
            files = [f for f in os.listdir(pdf_dir) if f.lower().endswith(".pdf") and os.path.isfile(os.path.join(pdf_dir, f))]
            logging.info(f"Found {len(files)} PDF files in {pdf_dir}.")
            # (任意) ファイル名でソート
            files.sort()
            # テンプレートに渡すデータを作成
            for filename in files:
                pdf_files_info.append({
                    "filename": filename,
                    # 静的ファイル配信マウントポイント /static-archives/ を使ったURL
                    "url": f"/static-archives/{filename}"
                })
        else:
            # archives ディレクトリが見つからない場合
            error_message = f"Archive directory not found: '{pdf_dir}'"
            logging.warning(error_message)

    except OSError as e:
        # ディレクトリ読み取り中にエラーが発生した場合
        error_message = f"Error reading archive directory '{pdf_dir}': {e}"
        logging.error(error_message)

    # archives.html テンプレートをレンダリングして返す
    return templates.TemplateResponse("archives.html", {
        "request": request,
        "pdf_files": pdf_files_info,
        "error": error_message # エラーがあればテンプレートに渡す
    })
# --- PDF一覧エンドポイントここまで ---