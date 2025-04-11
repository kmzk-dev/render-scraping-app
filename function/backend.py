import logging
import sys
import os
import time
import re
import shutil
from bs4 import BeautifulSoup
try:
    from .scraper import get_html_source, get_title, get_img_uri_list
    from .downloader import download_images
    from .converter import convert_webp_to_png, create_pdf_from_images
except ImportError as e:
    try:
        from function.scraper import get_html_source, get_title, get_img_uri_list
        from function.downloader import download_images
        from function.converter import convert_webp_to_png, create_pdf_from_images
    except ImportError as e2:
        logging.error(f"Failed to import function modules in backend.py: {e2}", exc_info=True)
        sys.exit(1)
        

def background_task(target_url: str):
    # 1. Get HTML source and parse it
    try:
        html_content = get_html_source(target_url)
        soup = BeautifulSoup(html_content, 'html.parser')
        page_title = get_title(soup)
        img_list = get_img_uri_list(soup)
        logging.info(f"  Title: {page_title}, Images Found: {len(img_list)}")
        if not img_list:
            logging.info("No images found. Task finished.")
            return
        logging.info(f"--- BG Task 1 Finished")
    except Exception as e:
        logging.info(f"Error during BG Task1: {e}", file=sys.stderr)
    # 2. Create temporary directories
    try:
        timestamp = str(int(time.time()))
        temp_filename = "temp" + timestamp + "img"
        output_base_dir = os.path.join("temporaries")
        # create parent directory
        parent_directory = os.path.join(output_base_dir,temp_filename) 
        os.makedirs(parent_directory, exist_ok=True)
        # create subdirectory
        save_directory = os.path.join(parent_directory, "downloaded")
        converted_directory = os.path.join(parent_directory, "converted")
        os.makedirs(save_directory, exist_ok=True)
        os.makedirs(converted_directory, exist_ok=True)
        logging.info(f"--- BG Task 2 Finished")
    except Exception as e:
        logging.info(f"Error during BG Task2: {e}", file=sys.stderr)
    # 3. Download images
    try:
        download_images(img_list, save_directory, temp_filename, ".webp", 0.25)
        logging.info(f"--- BG Task 3 Finished")
    except Exception as e:
        logging.info(f"Error during BG Task3: {e}", file=sys.stderr)
    #4. Convert images
    try:
        convert_webp_to_png(save_directory, converted_directory)
        logging.info(f"--- BG Task 4 Finished")
    except Exception as e:
        logging.info(f"Error during BG Task4: {e}", file=sys.stderr)
    # 5. Create PDF
    try:
        pdf_directory = os.path.join("archives")
        filename_true = re.sub(r'[\\/:*?"<>|]', '', page_title) # declare filename
        create_pdf_from_images(converted_directory, pdf_directory, filename_true)
        logging.info(f"--- BG Task 5 Finished")
    except Exception as e:
        logging.info(f"Error during BG Task5: {e}", file=sys.stderr)
    # 6. Clean up temporary directories
    try:
        shutil.rmtree(parent_directory)
        logging.info(f"--- BG Task 6 Finished")
    except Exception as e:
        logging.info(f"Error during BG Task6: {e}", file=sys.stderr)