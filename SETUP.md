# Setup Guide

This guide will help you set up all components of the Memory Graph system.

## Prerequisites

- Python 3.8+ installed
- Node.js 16+ and npm installed
- A modern web browser (Chrome or Firefox)
- (Optional) OpenAI API key for enhanced article analysis
- (Optional) Neo4j instance, Notion API access, and Obsidian vault path for integration sync

## Step-by-Step Setup

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create a virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# (Optional) Configure environment variables
cp .env.example .env
# Edit .env and add your OpenAI API key if you have one

# Run the backend server
python main.py
```

The backend API should now be running at `http://localhost:8000`

You can test it by visiting `http://localhost:8000/docs` to see the interactive API documentation.

### 2. Frontend Setup

Open a new terminal window:

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

The frontend should now be running at `http://localhost:3000`

### 3. Browser Extension Setup

#### For Chrome:

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top-right corner)
3. Click "Load unpacked"
4. Select the `browser-extension` directory from this project
5. The extension should now appear in your extensions list

#### For Firefox:

1. Open Firefox and navigate to `about:debugging#/runtime/this-firefox`
2. Click "Load Temporary Add-on"
3. Navigate to the `browser-extension` directory
4. Select the `manifest.json` file
5. The extension should now be loaded

#### Configure the Extension:

1. Click the extension icon in your browser toolbar
2. Set the backend URL to `http://localhost:8000` (should be default)
3. (Optional) Add your OpenAI API key in the extension options

### 4. Usage

#### Processing Bookmarks:

1. Make sure you have some bookmarks in your browser
2. Click the Memory Graph extension icon
3. Click "Process All Bookmarks"
4. Wait for the processing to complete
5. Check the frontend at `http://localhost:3000` to see your articles

#### Viewing Articles:

1. Open `http://localhost:3000` in your browser
2. Navigate through different sections:
   - Dashboard: Overview and quick actions
   - Articles: Browse and search all articles
   - Knowledge Graph: Visualize connections

#### Exporting to Obsidian:

1. Go to the Dashboard
2. Click "Convert All to Markdown"
3. Find the exported markdown files in `backend/exports/`
4. Copy these files to your Obsidian vault

#### Syncing to Neo4j / Notion / Obsidian Drafts:

1. Configure integration variables in `.env` (see `.env.example`)
2. Ensure Neo4j is running and the Notion API token has access to the inbox database
3. Call `POST /api/sync/full-pipeline?article_id={id}` to sync a processed article

## Troubleshooting

### Backend Issues

**Error: "No module named 'fastapi'"**
- Make sure you installed the requirements: `pip install -r requirements.txt`

**Error: "Port 8000 is already in use"**
- Another application is using port 8000. Either stop that application or change the port in `backend/main.py`

### Frontend Issues

**Error: "command not found: npm"**
- Install Node.js from https://nodejs.org/

**Error: "Failed to fetch articles"**
- Make sure the backend is running at `http://localhost:8000`
- Check if CORS is properly configured in the backend

### Browser Extension Issues

**Extension not loading**
- Make sure all required files are present in the `browser-extension` directory
- Check the browser console for error messages
- Ensure icon files exist in `browser-extension/icons/`

**Extension can't connect to backend**
- Verify the backend URL in extension options
- Make sure the backend is running
- Check browser console for CORS errors

**No bookmarks being processed**
- Grant the extension permission to access bookmarks
- Check if you have any bookmarks saved in your browser

## Development Tips

### Backend Development

- API documentation is available at `http://localhost:8000/docs`
- Database file is created at `backend/memory_graph.db`
- To reset the database, simply delete the `.db` file and restart the server

### Frontend Development

- Hot reload is enabled - changes will appear automatically
- API calls are proxied through Vite to avoid CORS issues in development
- Check browser console for React errors

### Extension Development

- After making changes to extension files, click the reload button in `chrome://extensions/`
- Use browser DevTools to debug popup and background scripts
- Background service worker console is accessible from the extension details page

## Optional: Production Deployment

### Backend

```bash
# Install production server
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000
```

### Frontend

```bash
# Build for production
npm run build

# Serve the dist folder with any static file server
```

### Extension

1. Create a ZIP file of the `browser-extension` directory
2. Submit to Chrome Web Store or Firefox Add-ons marketplace
3. Update the backend URL in the extension to point to your production API

## Support

For issues or questions, please check:
- The README.md file for detailed documentation
- The API documentation at `/docs`
- Browser console for error messages
- Python traceback for backend errors
