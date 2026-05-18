# AI Voice Analytics Media Management System

## Overview
This is an AI-based Voice-Controlled Media Management System designed to allow users to upload, edit, schedule, and analyze content using natural voice commands. It streamlines media operations and enhances accessibility.

## Features
- **Voice AI Control:** Process commands like "Upload video," "Show analytics," "Search tutorials," etc., via the Web Speech API and backend NLP processing.
- **Multilingual Support:** Handles basic commands in English and Hindi.
- **Media Library:** Upload (supports drag-and-drop), search, filter, and manage media files (videos, images, audio, documents).
- **Task Scheduler:** Schedule actions (e.g., publish, archive, delete) on media files automatically using APScheduler.
- **Analytics Dashboard:** Comprehensive visual analytics using Chart.js, including views, downloads, storage usage, upload trends, and voice intent distribution.

## Tech Stack
**Frontend:**
- HTML5, Vanilla JavaScript, CSS3
- Chart.js (for data visualization)
- Web Speech API (for voice recognition)

**Backend:**
- Python 3
- Flask (REST API)
- SQLite & SQLAlchemy (Database & ORM)
- APScheduler (Task scheduling)

## How to Run

### Method 1: Using the provided script (Windows)
Double-click `run_project.bat` in the root folder. It will automatically create a virtual environment, install dependencies, and start the server.

### Method 2: Manual Setup
1. Open a terminal in the `backend` folder.
2. Create a virtual environment: `python -m venv venv`
3. Activate the environment: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Mac/Linux)
4. Install requirements: `pip install -r requirements.txt`
5. Run the application: `python app.py`

Once running, the application is accessible at **http://localhost:5000**. The backend will automatically serve the frontend files.

## Project Structure
- `backend/`
  - `app.py`: Main Flask application and API routes.
  - `database.py`: SQLite models and initial data seeding.
  - `analytics.py`: Data aggregation logic for charts.
  - `scheduler.py`: Background job scheduling.
  - `voice_processor.py`: Intent and language detection module.
- `frontend/`
  - `index.html`: Main SPA interface.
  - `css/style.css`: Application styling (dark theme).
  - `js/`: JavaScript modules (`api.js`, `charts.js`, `voice.js`, `main.js`).

## Notes for Submission
- The database (`backend/media_analytics.db`) is auto-seeded with realistic mock data on the first run so that charts and the library look fully populated for your demo.
- If you want to reset the database, simply delete `media_analytics.db` and restart the server.
