# function/converter.py
from PIL import Image # Pillow ライブラリをインポート
import os
import sys # エラー出力用
import natsort  # 自然順ソートのためのライブラリ
import img2pdf # 画像からPDFを生成するためのライブラリ


def create_pdf_from_images(image_folder, output_pdf_dir, output_pdf_filename):
    """
    指定されたフォルダ内の画像ファイル(.png, .jpg, .jpeg)を自然順ソートし、
    単一のPDFファイルとして指定されたディレクトリに保存する。
    Args:
        image_folder (str): 画像ファイル(.pngなど)が格納されているディレクトリのパス。
        output_pdf_dir (str): 生成されるPDFファイルを保存するディレクトリのパス。
        output_pdf_filename (str): 生成されるPDFファイルの名前（拡張子 .pdf は除く）。
    Returns:
        bool: PDFの作成に成功した場合は True、失敗した場合は False。
    """
    # 画像フォルダの存在確認
    if not os.path.isdir(image_folder):
        print(f"Error: Image source directory not found: {image_folder}", file=sys.stderr)
        return False

    try:
        # 指定フォルダ内の画像ファイル(.png, .jpg, .jpeg)のフルパスリストを作成
        image_files = [
            os.path.join(image_folder, f)
            for f in os.listdir(image_folder)
            # isfileでファイルであること、endswithで拡張子を確認
            if os.path.isfile(os.path.join(image_folder, f)) and f.lower().endswith(('.png', '.jpg', '.jpeg'))
        ]

        if not image_files:
            print(f"Error: No compatible image files (.png, .jpg, .jpeg) found in {image_folder}", file=sys.stderr)
            return False

        sorted_image_files = natsort.natsorted(image_files)

        # PDFファイルへのフルパスを構築
        output_pdf_path = os.path.join(output_pdf_dir, f"{output_pdf_filename}.pdf")
        pdf_bytes = img2pdf.convert(sorted_image_files)
        with open(output_pdf_path, "wb") as f:
            f.write(pdf_bytes)
        print(f"Successfully created PDF: {output_pdf_path}")
        return True
    except Exception as e:
         print(f"An unexpected error occurred during PDF creation: {e}", file=sys.stderr)
         return False

def convert_webp_to_png(input_dir, output_dir):
    """
    指定された入力ディレクトリ内の全ての .webp ファイルを PNG 形式に変換し、
    指定された出力ディレクトリに同じファイル名（拡張子除く）で保存する。
    Args:
        input_dir (str): 変換元の .webp ファイルが格納されているディレクトリのパス。
        output_dir (str): 変換後の .png ファイルを保存するディレクトリのパス。
    Returns:
        bool: 処理が開始され、致命的なエラーなく完了した場合は True、
              入力ディレクトリが存在しない等で処理が開始できなかった場合は False。
    """

    # 入力ディレクトリの存在チェック
    if not os.path.isdir(input_dir):
        print(f"Error: Input directory not found: {input_dir}", file=sys.stderr)
        return False
    
    if not os.path.isdir(output_dir):
        print(f"Error: Input directory not found: {input_dir}", file=sys.stderr)
        return False


    # 入力ディレクトリ内のファイル一覧を取得
    try:
        # os.path.isfile を使ってファイルのみを対象にする
        files_in_dir = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
    except OSError as e:
         print(f"Error reading input directory {input_dir}: {e}", file=sys.stderr)
         return False

    for filename in files_in_dir:
        # ファイル拡張子が .webp かどうかをチェック (小文字にして比較)
        if filename.lower().endswith(".webp"):
            # 入力ファイルと出力ファイルのフルパスを作成
            input_path = os.path.join(input_dir, filename)
            # 出力ファイル名 (.webp を .png に置き換え)
            output_filename = os.path.splitext(filename)[0] + ".png"
            output_path = os.path.join(output_dir, output_filename)

            print(f"  Converting '{filename}' -> '{output_filename}'...")
            try:
                # PillowでWebP画像を開く
                with Image.open(input_path) as img:
                    img.save(output_path, "PNG")
            except Exception as e:
                # Pillowでの画像読み込み・保存エラーなど
                print(f"    Error converting file '{filename}': {e}", file=sys.stderr)

    print(f"--- Conversion Finished ---")
    # エラーがあっても処理自体は完了したとみなす場合はTrue
    return True