# AI Resume Screener

A smart, automated candidate shortlisting web application built with Python and Flask. The Screener evaluates resumes in bulk using regular expressions and keyword matching, extracts total years of experience, and streams the calculated match scores dynamically to a beautiful, mobile-responsive leaderboard.

## ✨ Features

- **Bulk Directory Scanning:** Point the system at an entire directory of resumes and let it automatically parse every `.pdf`, `.docx`, and `.txt` file using high-performance Python multiprocessing.
- **Drag & Drop Upload:** A modern, glassmorphic UI allowing direct file uploads or entire folder uploads directly from the browser.
- **Real-Time Streaming Results:** Powered by Server-Sent Events (SSE). Instead of waiting for a batch of 100+ resumes to finish processing, candidates slide into the leaderboard dynamically as soon as their background parsing completes!
- **Dynamic Leaderboard Sorting:** The frontend automatically calculates ranks and sorts incoming applicants from Highest Match to Lowest Match on the fly.
- **Role & Custom Skillset Evaluation:** Choose a predefined target role or input your own custom list of keywords (e.g., `python, sql, marketing, sales`) to evaluate.
- **Experience Extraction:** Automatically identifies, merges, and calculates total continuous career experience timelines from applicant resumes.
- **Fully Responsive UI:** A seamless experience on desktops, tablets, and smartphones.

## 🚀 Installation & Setup

### Prerequisites
- Python 3.9+ 

### 1. Install Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

### 2. Running Locally (Development)

To start the Flask development server (only accessible from your own computer):

```bash
python app.py
```
Then open `http://127.0.0.1:5000` or `http://localhost:5000` in your web browser.

### 3. Running on your Local Network (Windows Production)

If you want to share the app so your coworkers can access it on your local network/Wi-Fi, use a production server like Waitress:

```bash
pip install waitress
waitress-serve --host=0.0.0.0 --port=5000 app:app
```
Then find your local IP address (e.g., `192.168.1.15`). Your coworkers can access the app at `http://192.168.1.15:5000`.

## 📁 Project Structure

```bash
AI-Resume-Screener/
├── app.py                  # Main Flask backend application and SSE streams
├── requirements.txt        # Python dependencies
├── core/
│   ├── gdrive.py           # Google Drive integration utilities
│   ├── keywords.py         # Pre-defined roles and candidate keywords
│   ├── matcher.py          # Experience calculation and regex keyword matching logic
│   └── parser.py           # Text extraction logic for PDFs and Word Documents
├── templates/
│   ├── index.html          # Upload interface and scan configuration controls
│   └── results.html        # Streaming leaderboard and real-time DOM sorting
├── static/
│   └── style.css           # Glassmorphic, mobile-responsive styling and animations
└── uploads/                # Internal staging directory for uploaded resumes
```

## 🛠️ Usage

1. **Upload Resumes:** Navigate to the "Upload Resumes" tab to drag and drop single files or entire folders into the Screener's `uploads/` staging directory.
2. **Configure Scan:** On the "Scan Uploads" tab, select "Pre-defined Target Role" or input a "Custom Skillset" manually. 
3. **Analyze:** Click "Scan Uploads Directory". The Screener will bypass the Python GIL to parse your PDFs concurrently, streaming candidates directly to your screen with their Keyword Match % and Experience levels cleanly formatted.
