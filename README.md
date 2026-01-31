# Memory Graph - Knowledge Management System

A comprehensive system for managing and visualizing bookmarked articles using browser extension, backend API, and frontend interface.

## 📋 Features

- **Browser Extension**: Automatically traverse bookmarks, extract content, and classify articles using LLM
- **Backend API**: Store articles with domains and knowledge points, convert to Obsidian markdown
- **Frontend Interface**: View, search, and visualize article connections
- **Knowledge Graph**: Visualize connections between articles based on domains and knowledge points with pan/zoom filtering

## 🏗️ Architecture

The system consists of three main components:

1. **Browser Extension** (Chrome/Firefox)
   - Traverses user bookmarks
   - Extracts content from URLs
   - Uses LLM API to classify articles
   - Sends data to backend API

2. **Backend API** (FastAPI + Python)
   - RESTful API for article management
   - SQLite database for storage
   - LLM integration for content analysis
   - Markdown conversion for Obsidian export
   - Knowledge graph generation

3. **Frontend Interface** (React + Vite)
   - Dashboard with statistics
   - Article list with search and filtering
    - Knowledge graph visualization with domain/knowledge-point focus
   - Markdown export management

## 🚀 Quick Start

### Backend Setup

```bash
cd backend
pip install -r requirements.txt

# Optional: Set OpenAI API key for better analysis
export OPENAI_API_KEY=your-api-key-here

# Run the server
python main.py
```

The backend will be available at `http://localhost:8000`

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:3000`

### Browser Extension Setup

1. Open Chrome/Firefox and navigate to extensions page
   - Chrome: `chrome://extensions/`
   - Firefox: `about:addons`

2. Enable "Developer mode"

3. Click "Load unpacked" and select the `browser-extension` directory

4. Configure backend URL in extension options (default: `http://localhost:8000`)

5. Click the extension icon and process your bookmarks

## 📖 Usage

### 1. Process Bookmarks

1. Install the browser extension
2. Click the extension icon
3. Click "Process All Bookmarks" to analyze all bookmarks
4. Wait for processing to complete

### 2. View Articles

1. Open the frontend at `http://localhost:3000`
2. Navigate to "Articles" to view all processed articles
3. Use search and filters to find specific articles
4. Click on an article to view details and related articles

### 3. Export to Obsidian

1. Go to Dashboard
2. Click "Convert All to Markdown"
3. Markdown files will be created in `backend/exports/` directory
4. Copy these files to your Obsidian vault

### 4. Visualize Knowledge Graph

1. Navigate to "Knowledge Graph" in the frontend
2. View connections between articles, domains, and knowledge points
3. Filter by a specific domain or knowledge point to focus the graph
4. Pan/zoom the canvas and click article nodes to open their URLs

### 5. Notion / Obsidian / Neo4j Integration

See [INTEGRATION_PLAN.md](INTEGRATION_PLAN.md) for a
practical, layered integration design that positions Neo4j as the source of truth, Obsidian as the
writing surface, and Notion as the execution dashboard.

## 🔧 API Endpoints

### Articles

- `GET /api/articles` - Get all articles (with pagination)
- `GET /api/articles/{id}` - Get specific article
- `POST /api/articles` - Create new article
- `POST /api/articles/analyze-url` - Extract and analyze URL
- `GET /api/articles/{id}/related` - Get related articles

### Domains & Knowledge Points

- `GET /api/domains` - Get all domains
- `GET /api/knowledge-points` - Get all knowledge points

### Tasks

- `POST /api/tasks/convert-to-markdown` - Convert articles to Obsidian markdown
- `GET /api/knowledge-graph` - Get knowledge graph data

## 📁 Project Structure

```
memory-graph/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── database.py          # Database models
│   ├── schemas.py           # Pydantic schemas
│   ├── services.py          # LLM and content extraction
│   ├── tasks.py             # Markdown conversion and graph
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Main React app
│   │   ├── components/      # React components
│   │   └── index.css        # Styles
│   ├── package.json         # Node dependencies
│   └── vite.config.js       # Vite configuration
├── browser-extension/
│   ├── manifest.json        # Extension manifest
│   ├── popup.html           # Extension popup UI
│   ├── popup.js             # Popup logic
│   ├── background.js        # Background service worker
│   ├── options.html         # Settings page
│   └── options.js           # Settings logic
└── README.md
```

## 🔐 Environment Variables

### Backend

- `OPENAI_API_KEY` - OpenAI API key for enhanced article analysis (optional)

If not provided, the system will use simple keyword-based analysis as fallback.

## 🛠️ Technology Stack

### Backend
- FastAPI - Modern Python web framework
- SQLAlchemy - ORM for database
- SQLite - Lightweight database
- OpenAI API - For article analysis
- BeautifulSoup - HTML parsing
- Pydantic - Data validation

### Frontend
- React 18 - UI framework
- Vite - Build tool
- Axios - HTTP client
- Canvas API - Graph visualization

### Browser Extension
- Manifest V3 - Chrome extension format
- Chrome Bookmarks API - Access bookmarks
- Chrome Storage API - Store settings

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

MIT License

## 🔮 Future Enhancements

- [ ] Advanced graph visualization with D3.js or similar
- [ ] Support for more LLM providers (Claude, Gemini, etc.)
- [ ] Article summarization
- [ ] Duplicate detection
- [ ] Tag management
- [ ] Notion / Obsidian / Neo4j integration tooling (sync workers, webhooks, CLI)
- [ ] Scheduled bookmark processing
- [ ] Browser extension for Firefox
- [ ] Mobile app support
