import logging
import sys 
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s',
    stream=sys.stdout 
)
import os
from fastapi import FastAPI, Request, Form, BackgroundTasks, status
from fastapi.responses import HTMLResponse,RedirectResponse 
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles 
from function.backend import background_task

# --- Setting ---
app = FastAPI(title="Simple URL Input Form") # initialize FastAPI instance
templates = Jinja2Templates(directory="templates") #tenmplates directory
local_archives_dir = "archives"
try:
    app.mount("/static-archives", StaticFiles(directory=local_archives_dir), name="static_archives")
except Exception as e:
    logging.error(f"Failed to mount static directory: {e}")

#index page endpoint
@app.get("/", response_class=HTMLResponse)
async def read_form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

#Background task endpoint:
@app.post("/submit-url/")
async def accept_url_and_start_processing(
    background_tasks: BackgroundTasks,
    url: str = Form(...)
):
    background_tasks.add_task(background_task, url)
    return RedirectResponse(url="/archives/", status_code=status.HTTP_303_SEE_OTHER)

#PDF list Endpoint:
@app.get("/archives/", response_class=HTMLResponse)
async def show_archives(request: Request):
    pdf_files_info = []
    error_message = None
    try:
        files = [f for f in os.listdir(local_archives_dir) if f.lower().endswith(".pdf") and os.path.isfile(os.path.join(local_archives_dir, f))]
        for filename in files:
            pdf_files_info.append({
                "filename": filename,
                "url": f"/static-archives/{filename}" # static file mounted directory
            })
    except Exception as e:
        error_message = f"An unexpected error occurred while reading the archive directory: {e}"
        logging.error(error_message)

    return templates.TemplateResponse("archives.html", {
        "request": request,
        "pdf_files": pdf_files_info,
        "error": error_message
    })