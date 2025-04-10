from selenium import webdriver
from selenium.common.exceptions import WebDriverException, TimeoutException # TimeoutExceptionを追加
from selenium.webdriver.common.by import By # WebDriverWait用にByを追加
from selenium.webdriver.support.ui import WebDriverWait # WebDriverWaitを追加
from selenium.webdriver.support import expected_conditions as EC # WebDriverWait用にECを追加
import sys # エラーメッセージ出力用にsysを追加

def get_img_uri_list(page_soup):
    """
    BeautifulSoupオブジェクトから、ID 'post-comic' 内の全てのimgタグのsrc属性を取得し、
    リストとして返す。'#post-comic' が存在しない場合は空リストを返す。
    """
    img_uri_list = []
    post_comic_element = page_soup.select_one('#post-comic')
    if post_comic_element is not None:
        img_tags = post_comic_element.select('img')
        print(f"Found element with ID #post-comic. Found {len(img_tags)} img tags within it.")
        for img_tag in img_tags:
            img_src = img_tag.get('src')
            img_uri_list.append(img_src)
    else:
        print("Warning: Element with ID '#post-comic' not found on the page.")
        
    return img_uri_list

def get_title(page_soup):
  title = page_soup.title.get_text()
  return title

def get_html_source(uri, wait_time=3):
    """
    指定されたURLにSeleniumを使ってアクセスし、ページのHTMLソースコードを文字列として返す。
    信頼性向上のため、time.sleep() の代わりに明示的な待機(WebDriverWait)を使用する。
    """
    print("Initializing get_html_source...")
    html_source = None #戻り値を初期化
    driver = None # finallyブロックでdriver変数を参照できるように初期化
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    try:
        print("Initializing WebDriver...")
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(uri)
        # --- 明示的な待機 (Explicit Wait) ---
        print("Navigation initiated. Waiting for page content to load...")
        try:
            WebDriverWait(driver, wait_time).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            print(f"Page body detected after waiting.")
        except TimeoutException:
            print(f"Warning: Page load or element presence timed out after {wait_time} seconds. Attempting to get source anyway.")

        html_source = driver.page_source
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
    finally:
        # エラー発生有無に関わらず、WebDriverを確実に終了する
        if driver:
            driver.quit()
            print("WebDriver quit.")

    return html_source # 取得したHTML文字列を返す