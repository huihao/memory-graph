# Memory Graph System - Architecture Overview

## System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                         User's Browser                           │
│                                                                   │
│  ┌─────────────────────┐         ┌──────────────────────┐       │
│  │  Browser Extension  │         │   Frontend Web App   │       │
│  │                     │         │                      │       │
│  │  • Popup UI         │         │  • Dashboard         │       │
│  │  • Options Page     │         │  • Article List      │       │
│  │  • Background       │         │  • Article Details   │       │
│  │    Service Worker   │         │  • Knowledge Graph   │       │
│  │  • Bookmark         │         │                      │       │
│  │    Traversal        │         │  React + Vite        │       │
│  └──────────┬──────────┘         └──────────┬───────────┘       │
│             │                               │                    │
└─────────────┼───────────────────────────────┼────────────────────┘
              │                               │
              │ HTTP POST/GET                 │ HTTP GET
              │ /api/articles/analyze-url     │ /api/articles
              │                               │ /api/knowledge-graph
              │                               │
              └───────────────┬───────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │      Backend API Server       │
              │                               │
              │  FastAPI Application          │
              │                               │
              │  ┌─────────────────────────┐  │
              │  │   API Endpoints         │  │
              │  │   • Articles            │  │
              │  │   • Domains             │  │
              │  │   • Knowledge Points    │  │
              │  │   • Tasks               │  │
              │  │   • Knowledge Graph     │  │
              │  └──────────┬──────────────┘  │
              │             │                  │
              │  ┌──────────▼──────────────┐  │
              │  │   Business Logic        │  │
              │  │   • Content Extraction  │  │
              │  │   • LLM Analysis        │  │
              │  │   • Markdown Convert    │  │
              │  │   • Graph Generation    │  │
              │  └──────────┬──────────────┘  │
              │             │                  │
              │  ┌──────────▼──────────────┐  │
              │  │   SQLite Database       │  │
              │  │   • Articles            │  │
              │  │   • Domains             │  │
              │  │   • Knowledge Points    │  │
              │  │   • Relationships       │  │
              │  └─────────────────────────┘  │
              │                               │
              └───────────────┬───────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │     File System Output        │
              │                               │
              │  exports/                     │
              │  └── *.md (Obsidian format)   │
              │                               │
              └───────────────────────────────┘
```

## Data Flow

### 1. Bookmark Processing Flow

```
User Bookmarks
      │
      ▼
Browser Extension
      │
      ├─► Traverse Bookmarks API
      │
      ├─► For each URL:
      │   │
      │   ├─► Extract HTML Content
      │   │   (BeautifulSoup)
      │   │
      │   ├─► Analyze with LLM
      │   │   (OpenAI or keyword-based)
      │   │
      │   └─► POST to Backend API
      │       /api/articles/analyze-url
      │
      ▼
Backend Processing
      │
      ├─► Parse & Extract Domains
      │
      ├─► Parse & Extract Knowledge Points
      │
      ├─► Create/Update Database Records
      │   │
      │   ├─► Article Record
      │   ├─► Domain Records
      │   ├─► Knowledge Point Records
      │   └─► Relationships
      │
      └─► Return Result to Extension
```

### 2. Article Viewing Flow

```
User Opens Frontend
      │
      ▼
React App Loads
      │
      ├─► GET /api/articles
      │   └─► Display Article List
      │
      ├─► GET /api/domains
      │   └─► Display Filter Options
      │
      └─► GET /api/knowledge-graph
          └─► Display Graph Visualization
```

### 3. Markdown Export Flow

```
User Clicks "Convert to Markdown"
      │
      ▼
POST /api/tasks/convert-to-markdown
      │
      ├─► Fetch Articles from Database
      │
      ├─► For each Article:
      │   │
      │   ├─► Format as Markdown
      │   │   • Title
      │   │   • Metadata (tags, dates)
      │   │   • Domains (as links)
      │   │   • Knowledge Points (as links)
      │   │   • Content
      │   │   • Source URL
      │   │
      │   └─► Write to exports/*.md
      │
      └─► Return List of Created Files
```

## Database Schema

```
┌─────────────────────┐
│      Articles       │
│─────────────────────│
│ id (PK)             │
│ url (unique)        │
│ title               │
│ content             │
│ summary             │
│ created_at          │
│ updated_at          │
│ markdown_path       │
└──────────┬──────────┘
           │
           │ many-to-many
           │
    ┌──────┴───────┐
    │              │
    ▼              ▼
┌─────────┐   ┌──────────────┐
│ Domains │   │ Knowledge    │
│─────────│   │ Points       │
│ id (PK) │   │──────────────│
│ name    │   │ id (PK)      │
│ desc    │   │ name         │
└─────────┘   │ description  │
              └──────────────┘
```

## Technology Stack

### Backend
- **Framework**: FastAPI 0.104.1
- **Database**: SQLite + SQLAlchemy 2.0
- **Web Scraping**: BeautifulSoup4 4.12.2, aiohttp 3.9.1
- **AI/LLM**: OpenAI API 1.3.7 (optional)
- **Data Validation**: Pydantic 2.5.0

### Frontend
- **Framework**: React 18.2.0
- **Build Tool**: Vite 5.0.5
- **HTTP Client**: Axios 1.6.2
- **Routing**: React Router 6.20.0
- **Visualization**: Canvas API, D3.js (optional)

### Browser Extension
- **Manifest**: Version 3 (Chrome/Firefox compatible)
- **APIs Used**: 
  - Chrome Bookmarks API
  - Chrome Storage API
  - Fetch API for backend communication

## Key Features

### 1. Automatic Content Extraction
- Extracts article content from any URL
- Cleans HTML and extracts text
- Preserves title and main content

### 2. AI-Powered Classification
- Uses OpenAI GPT for intelligent domain detection
- Identifies key knowledge points and concepts
- Falls back to keyword-based analysis if API key not available

### 3. Knowledge Graph
- Visualizes connections between articles
- Links articles in same domains
- Shows articles sharing knowledge points
- Interactive graph visualization

### 4. Obsidian Integration
- Exports to standard Markdown format
- Uses Obsidian wiki-link syntax [[Domain]]
- Includes frontmatter with metadata
- Preserves relationships through links

### 5. Notion / Obsidian / Neo4j Integration

The integration plan positions Neo4j as the source of truth, Obsidian as the writing surface, and Notion as the execution layer. See [INTEGRATION_PLAN.md](INTEGRATION_PLAN.md) for the full architecture, sync rules, and conflict-resolution strategy.

### 6. Search & Filter
- Full-text search across articles
- Filter by domain
- Filter by knowledge point
- Sort by various criteria

## File Organization

```
memory-graph/
├── README.md              # Main documentation
├── SETUP.md              # Setup instructions
├── API.md                # API documentation
├── start.sh              # Quick start script
├── .gitignore            # Git ignore rules
│
├── backend/              # Python backend
│   ├── main.py           # FastAPI app & routes
│   ├── database.py       # SQLAlchemy models
│   ├── schemas.py        # Pydantic schemas
│   ├── services.py       # LLM & content extraction
│   ├── tasks.py          # Markdown & graph services
│   ├── test_setup.py     # Setup verification
│   ├── requirements.txt  # Python dependencies
│   └── .env.example      # Environment template
│
├── frontend/             # React frontend
│   ├── src/
│   │   ├── main.jsx      # App entry point
│   │   ├── App.jsx       # Main app component
│   │   ├── index.css     # Global styles
│   │   └── components/   # React components
│   │       ├── Dashboard.jsx
│   │       ├── ArticleList.jsx
│   │       ├── ArticleDetail.jsx
│   │       └── KnowledgeGraph.jsx
│   ├── index.html        # HTML template
│   ├── package.json      # Node dependencies
│   └── vite.config.js    # Vite configuration
│
└── browser-extension/    # Chrome/Firefox extension
    ├── manifest.json     # Extension manifest
    ├── popup.html        # Popup UI
    ├── popup.js          # Popup logic
    ├── background.js     # Service worker
    ├── options.html      # Settings UI
    ├── options.js        # Settings logic
    └── icons/            # Extension icons
        ├── icon16.png
        ├── icon48.png
        ├── icon128.png
        └── icon.svg
```

## Deployment Considerations

### Development
- Backend: `python main.py` (localhost:8000)
- Frontend: `npm run dev` (localhost:3000)
- Extension: Load unpacked in browser

### Production
- Backend: Deploy with Gunicorn/Uvicorn + Nginx
- Frontend: Build with `npm run build`, serve static files
- Extension: Package and submit to browser stores
- Database: Consider PostgreSQL for production
- Add authentication and rate limiting
- Configure CORS properly
- Use HTTPS for all connections
