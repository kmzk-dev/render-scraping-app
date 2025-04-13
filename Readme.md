# Render Scraping App

A simple FastAPI-based web application that accepts URLs, processes them in the background, and displays a list of archived PDFs. This application demonstrates the use of FastAPI for building web applications with background task handling and static file serving.

## Features

- **URL Submission**: Submit URLs via a web form for processing.
- **Background Task Handling**: Asynchronously process submitted URLs without blocking the user interface.
- **PDF Archive Management**: List and serve archived PDF files from a static directory.
- **Error Logging**: Comprehensive logging for troubleshooting errors.

## Requirements

- **Python Version**: Requires Python 3.8 or higher.
- **Dependencies**:
  - `fastapi`
  - `uvicorn`
  - `jinja2`
  - Any other dependencies listed in `requirements.txt`

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/kmzk-dev/render-scraping-app.git
   cd render-scraping-app