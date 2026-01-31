# API Documentation

Memory Graph REST API provides endpoints for managing articles, domains, knowledge points, and generating knowledge graphs.

## Base URL

```
http://localhost:8000
```

## Interactive Documentation

FastAPI provides automatic interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Authentication

Currently, the API does not require authentication. In a production environment, you should add authentication using JWT tokens or API keys.

## Endpoints

### Root

#### GET /

Get API information.

**Response**
```json
{
  "message": "Memory Graph API",
  "version": "1.0.0"
}
```

---

### Articles

#### POST /api/articles

Create a new article.

**Request Body**
```json
{
  "url": "https://example.com/article",
  "title": "Article Title",
  "content": "Article content...",
  "summary": "Brief summary (optional)",
  "domain_names": ["Web Development", "JavaScript"],
  "knowledge_point_names": ["React Hooks", "State Management"]
}
```

**Response**
```json
{
  "id": 1,
  "url": "https://example.com/article",
  "title": "Article Title",
  "content": "Article content...",
  "summary": "Brief summary",
  "created_at": "2024-01-31T10:00:00",
  "updated_at": "2024-01-31T10:00:00",
  "markdown_path": null,
  "domains": [
    {
      "id": 1,
      "name": "Web Development",
      "description": null,
      "created_at": "2024-01-31T10:00:00"
    }
  ],
  "knowledge_points": [
    {
      "id": 1,
      "name": "React Hooks",
      "description": null,
      "created_at": "2024-01-31T10:00:00"
    }
  ]
}
```

#### GET /api/articles

Get all articles with pagination.

**Query Parameters**
- `skip` (integer, optional): Number of articles to skip (default: 0)
- `limit` (integer, optional): Maximum number of articles to return (default: 100)

**Response**
```json
{
  "articles": [
    {
      "id": 1,
      "url": "https://example.com/article",
      "title": "Article Title",
      "content": "Article content...",
      "summary": "Brief summary",
      "created_at": "2024-01-31T10:00:00",
      "updated_at": "2024-01-31T10:00:00",
      "markdown_path": "/path/to/markdown.md",
      "domains": [...],
      "knowledge_points": [...]
    }
  ],
  "total": 1
}
```

#### GET /api/articles/{article_id}

Get a specific article by ID.

**Path Parameters**
- `article_id` (integer): Article ID

**Response**
```json
{
  "id": 1,
  "url": "https://example.com/article",
  "title": "Article Title",
  ...
}
```

#### POST /api/articles/analyze-url

Extract content from a URL and analyze it with LLM. This is the main endpoint used by the browser extension.

**Query Parameters**
- `url` (string): The URL to analyze

**Response**
```json
{
  "status": "created",
  "article_id": 1,
  "article": {
    "id": 1,
    "url": "https://example.com/article",
    "title": "Extracted Title",
    "content": "Extracted content...",
    "domains": [...],
    "knowledge_points": [...]
  }
}
```

If the article already exists:
```json
{
  "status": "exists",
  "article_id": 1,
  "article": {...}
}
```

#### GET /api/articles/{article_id}/related

Get articles related to a specific article.

**Path Parameters**
- `article_id` (integer): Article ID

**Response**
```json
{
  "by_domain": [
    {
      "id": 2,
      "title": "Related Article 1",
      ...
    }
  ],
  "by_knowledge_point": [
    {
      "id": 3,
      "title": "Related Article 2",
      ...
    }
  ]
}
```

---

### Domains

#### GET /api/domains

Get all domains.

**Response**
```json
[
  {
    "id": 1,
    "name": "Web Development",
    "description": null,
    "created_at": "2024-01-31T10:00:00"
  }
]
```

---

### Knowledge Points

#### GET /api/knowledge-points

Get all knowledge points.

**Response**
```json
[
  {
    "id": 1,
    "name": "React Hooks",
    "description": null,
    "created_at": "2024-01-31T10:00:00"
  }
]
```

---

### Tasks

#### POST /api/tasks/convert-to-markdown

Convert all articles to Obsidian markdown format.

**Query Parameters**
- `limit` (integer, optional): Maximum number of articles to convert

**Response**
```json
{
  "status": "success",
  "converted": 10,
  "files": [
    "/path/to/export/Article-Title.md",
    ...
  ]
}
```

---

### Knowledge Graph

#### GET /api/knowledge-graph

Get knowledge graph data for visualization.

**Query Parameters**
- `domain_id` (integer, optional): Focus graph on a specific domain
- `knowledge_point_id` (integer, optional): Focus graph on a specific knowledge point

**Response**
```json
{
  "nodes": [
    {
      "id": "article_1",
      "label": "Article Title",
      "type": "article",
      "url": "https://example.com/article",
      "icon": "📄",
      "size": 10
    },
    {
      "id": "domain_1",
      "label": "Web Development",
      "type": "domain",
      "icon": "🧭",
      "size": 12
    },
    {
      "id": "kp_1",
      "label": "React Hooks",
      "type": "knowledge_point",
      "icon": "💡",
      "size": 12
    }
  ],
  "edges": [
    {
      "source": "article_1",
      "target": "domain_1",
      "type": "belongs_to"
    },
    {
      "source": "article_1",
      "target": "kp_1",
      "type": "covers"
    },
    {
      "source": "article_1",
      "target": "article_2",
      "type": "related_articles",
      "shared_domains": ["Web Development"],
      "shared_knowledge_points": ["React Hooks"],
      "weight": 2
    }
  ],
  "context": {
    "domain": "Web Development",
    "knowledge_point": null
  }
}
```

---

### Integration Plan

The Notion / Obsidian / Neo4j integration architecture is documented in [INTEGRATION_PLAN.md](INTEGRATION_PLAN.md). It describes data ownership, sync rules, and the API surface you will eventually expose for syncing and conflict resolution.

## Error Responses

All endpoints may return error responses in the following format:

**400 Bad Request**
```json
{
  "detail": "Article with this URL already exists"
}
```

**404 Not Found**
```json
{
  "detail": "Article not found"
}
```

**422 Validation Error**
```json
{
  "detail": [
    {
      "loc": ["body", "url"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**500 Internal Server Error**
```json
{
  "detail": "Internal server error message"
}
```

---

## CORS

The API is configured to accept requests from any origin in development mode. In production, you should configure specific allowed origins.

---

## Rate Limiting

Currently, there is no rate limiting implemented. For production use, consider adding rate limiting middleware.

---

## Examples

### Using curl

**Create an article:**
```bash
curl -X POST "http://localhost:8000/api/articles" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/article",
    "title": "My Article",
    "content": "Article content",
    "domain_names": ["Technology"],
    "knowledge_point_names": ["API Design"]
  }'
```

**Get all articles:**
```bash
curl "http://localhost:8000/api/articles?limit=10"
```

**Analyze a URL:**
```bash
curl -X POST "http://localhost:8000/api/articles/analyze-url?url=https://example.com/article"
```

### Using Python

```python
import requests

# Analyze a URL
response = requests.post(
    "http://localhost:8000/api/articles/analyze-url",
    params={"url": "https://example.com/article"}
)
print(response.json())

# Get all articles
response = requests.get("http://localhost:8000/api/articles")
data = response.json()
print(f"Total articles: {data['total']}")
```

### Using JavaScript

```javascript
// Analyze a URL
fetch('http://localhost:8000/api/articles/analyze-url?url=https://example.com/article', {
  method: 'POST'
})
  .then(response => response.json())
  .then(data => console.log(data));

// Get all articles
fetch('http://localhost:8000/api/articles')
  .then(response => response.json())
  .then(data => console.log(`Total articles: ${data.total}`));
```
