"""
Unit tests for FastAPI endpoints in main.py
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool
from database import Base, Article, Domain, KnowledgePoint, get_db

# Import app
from main import app

# Create a test engine with static pool for in-memory SQLite
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def test_db():
    """Create database tables and provide a session"""
    Base.metadata.create_all(bind=test_engine)
    
    # Create a session for setup/teardown
    connection = test_engine.connect()
    session = TestingSessionLocal(bind=connection)
    
    def override_get_db():
        try:
            yield session
        finally:
            pass  # Don't close - we manage this in the fixture
    
    app.dependency_overrides[get_db] = override_get_db
    
    yield session
    
    session.close()
    connection.close()
    Base.metadata.drop_all(bind=test_engine)
    app.dependency_overrides.clear()


@pytest.fixture
def client(test_db):
    """Create a test client"""
    return TestClient(app)


@pytest.fixture
def db(test_db):
    """Alias for test_db for cleaner test code"""
    return test_db


@pytest.fixture
def sample_domain(db):
    """Create a sample domain"""
    domain = Domain(name="Test Domain")
    db.add(domain)
    db.commit()
    db.refresh(domain)
    return domain


@pytest.fixture
def sample_knowledge_point(db):
    """Create a sample knowledge point"""
    kp = KnowledgePoint(name="Test KP")
    db.add(kp)
    db.commit()
    db.refresh(kp)
    return kp


@pytest.fixture
def sample_article(db, sample_domain, sample_knowledge_point):
    """Create a sample article with relationships"""
    article = Article(
        url="https://example.com/test",
        title="Test Article",
        content="Test content",
        summary="Test summary"
    )
    article.domains.append(sample_domain)
    article.knowledge_points.append(sample_knowledge_point)
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


class TestRootEndpoints:
    """Tests for root and health endpoints"""
    
    def test_root(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Memory Graph API"
        assert data["version"] == "1.0.0"
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["version"] == "1.0.0"


class TestStatsEndpoint:
    """Tests for stats endpoint"""
    
    def test_stats_empty(self, client):
        """Test stats with empty database"""
        response = client.get("/api/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total_articles"] == 0
        assert data["total_domains"] == 0
        assert data["total_knowledge_points"] == 0
        assert data["recent_articles"] == 0
        assert data["top_domains"] == []
    
    def test_stats_with_data(self, client, sample_article):
        """Test stats with data"""
        response = client.get("/api/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total_articles"] == 1
        assert data["total_domains"] == 1
        assert data["total_knowledge_points"] == 1
        assert data["recent_articles"] == 1  # Created today
    
    def test_stats_top_domains(self, client, db, sample_article):
        """Test stats includes top domains with article counts"""
        response = client.get("/api/stats")
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["top_domains"]) == 1
        assert data["top_domains"][0]["name"] == "Test Domain"
        assert data["top_domains"][0]["article_count"] == 1


class TestArticleEndpoints:
    """Tests for article CRUD endpoints"""
    
    def test_create_article(self, client):
        """Test creating an article"""
        response = client.post("/api/articles", json={
            "url": "https://example.com/new",
            "title": "New Article",
            "content": "Content",
            "summary": "Summary",
            "domain_names": ["New Domain"],
            "knowledge_point_names": ["New KP"]
        })
        assert response.status_code == 200
        data = response.json()
        assert data["url"] == "https://example.com/new"
        assert data["title"] == "New Article"
        assert len(data["domains"]) == 1
        assert len(data["knowledge_points"]) == 1
    
    def test_create_article_duplicate_url(self, client, sample_article):
        """Test creating article with duplicate URL fails"""
        response = client.post("/api/articles", json={
            "url": sample_article.url,
            "title": "Duplicate",
            "domain_names": [],
            "knowledge_point_names": []
        })
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
    
    def test_create_article_with_existing_domain(self, client, sample_domain):
        """Test creating article reuses existing domain"""
        response = client.post("/api/articles", json={
            "url": "https://example.com/new",
            "title": "New Article",
            "domain_names": [sample_domain.name],
            "knowledge_point_names": []
        })
        assert response.status_code == 200
        data = response.json()
        assert len(data["domains"]) == 1
        assert data["domains"][0]["id"] == sample_domain.id
    
    def test_get_articles_empty(self, client):
        """Test getting articles when empty"""
        response = client.get("/api/articles")
        assert response.status_code == 200
        data = response.json()
        assert data["articles"] == []
        assert data["total"] == 0
    
    def test_get_articles_with_data(self, client, sample_article):
        """Test getting articles with data"""
        response = client.get("/api/articles")
        assert response.status_code == 200
        data = response.json()
        assert len(data["articles"]) == 1
        assert data["total"] == 1
        assert data["articles"][0]["id"] == sample_article.id
    
    def test_get_articles_pagination(self, client, db):
        """Test article pagination"""
        # Create 5 articles
        for i in range(5):
            article = Article(url=f"https://example.com/{i}", title=f"Article {i}")
            db.add(article)
        db.commit()
        
        # Test skip
        response = client.get("/api/articles?skip=2&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["articles"]) == 2
        assert data["total"] == 5
    
    def test_get_article_by_id(self, client, sample_article):
        """Test getting article by ID"""
        response = client.get(f"/api/articles/{sample_article.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_article.id
        assert data["title"] == sample_article.title
    
    def test_get_article_not_found(self, client):
        """Test getting non-existent article"""
        response = client.get("/api/articles/999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_delete_article(self, client, sample_article, db):
        """Test deleting an article"""
        article_id = sample_article.id
        response = client.delete(f"/api/articles/{article_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "deleted"
        assert data["article_id"] == article_id
        
        # Verify article is deleted
        db.expire_all()
        article = db.query(Article).filter(Article.id == article_id).first()
        assert article is None
    
    def test_delete_article_not_found(self, client):
        """Test deleting non-existent article"""
        response = client.delete("/api/articles/999")
        assert response.status_code == 404


class TestSearchEndpoint:
    """Tests for article search endpoint"""
    
    def test_search_no_query(self, client, sample_article):
        """Test search without query returns all"""
        response = client.get("/api/articles/search")
        assert response.status_code == 200
        data = response.json()
        assert len(data["articles"]) == 1
        assert data["total"] == 1
    
    def test_search_by_title(self, client, sample_article):
        """Test search by title"""
        response = client.get(f"/api/articles/search?q={sample_article.title}")
        assert response.status_code == 200
        data = response.json()
        assert len(data["articles"]) == 1
    
    def test_search_by_url(self, client, sample_article):
        """Test search by URL"""
        response = client.get("/api/articles/search?q=example.com")
        assert response.status_code == 200
        data = response.json()
        assert len(data["articles"]) == 1
    
    def test_search_by_content(self, client, sample_article):
        """Test search by content"""
        response = client.get("/api/articles/search?q=content")
        assert response.status_code == 200
        data = response.json()
        assert len(data["articles"]) == 1
    
    def test_search_no_results(self, client, sample_article):
        """Test search with no results"""
        response = client.get("/api/articles/search?q=nonexistent")
        assert response.status_code == 200
        data = response.json()
        assert len(data["articles"]) == 0
        assert data["total"] == 0
    
    def test_search_by_domain(self, client, sample_article, sample_domain):
        """Test search by domain ID"""
        response = client.get(f"/api/articles/search?domain_id={sample_domain.id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data["articles"]) == 1
    
    def test_search_by_knowledge_point(self, client, sample_article, sample_knowledge_point):
        """Test search by knowledge point ID"""
        response = client.get(f"/api/articles/search?knowledge_point_id={sample_knowledge_point.id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data["articles"]) == 1
    
    def test_search_pagination(self, client, db):
        """Test search pagination"""
        for i in range(25):
            article = Article(url=f"https://example.com/{i}", title=f"Article {i}")
            db.add(article)
        db.commit()
        
        response = client.get("/api/articles/search?skip=10&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["articles"]) == 10
        assert data["skip"] == 10
        assert data["limit"] == 10
        assert data["has_more"] is True


class TestDomainEndpoints:
    """Tests for domain endpoints"""
    
    def test_get_domains_empty(self, client):
        """Test getting domains when empty"""
        response = client.get("/api/domains")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_get_domains_with_data(self, client, sample_domain):
        """Test getting domains with data"""
        response = client.get("/api/domains")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == sample_domain.name


class TestKnowledgePointEndpoints:
    """Tests for knowledge point endpoints"""
    
    def test_get_knowledge_points_empty(self, client):
        """Test getting knowledge points when empty"""
        response = client.get("/api/knowledge-points")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_get_knowledge_points_with_data(self, client, sample_knowledge_point):
        """Test getting knowledge points with data"""
        response = client.get("/api/knowledge-points")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == sample_knowledge_point.name


class TestMarkdownConversionEndpoint:
    """Tests for markdown conversion endpoint"""
    
    def test_convert_to_markdown(self, client, sample_article):
        """Test converting articles to markdown"""
        with patch('main.markdown_converter.batch_convert') as mock_convert:
            mock_convert.return_value = ["/path/to/file.md"]
            
            response = client.post("/api/tasks/convert-to-markdown")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["converted"] == 1
    
    def test_convert_to_markdown_with_limit(self, client, sample_article):
        """Test converting with limit"""
        with patch('main.markdown_converter.batch_convert') as mock_convert:
            mock_convert.return_value = []
            
            response = client.post("/api/tasks/convert-to-markdown?limit=5")
            assert response.status_code == 200
            mock_convert.assert_called_once()


class TestRelatedArticlesEndpoint:
    """Tests for related articles endpoint"""
    
    def test_get_related_articles(self, client, sample_article):
        """Test getting related articles"""
        with patch('main.knowledge_graph_service.find_related_articles') as mock_find:
            mock_find.return_value = {"by_domain": [], "by_knowledge_point": []}
            
            response = client.get(f"/api/articles/{sample_article.id}/related")
            assert response.status_code == 200
            data = response.json()
            assert "by_domain" in data
            assert "by_knowledge_point" in data


class TestKnowledgeGraphEndpoint:
    """Tests for knowledge graph endpoint"""
    
    def test_get_knowledge_graph(self, client):
        """Test getting knowledge graph data"""
        with patch('main.knowledge_graph_service.get_knowledge_graph_data') as mock_get:
            mock_get.return_value = {"nodes": [], "edges": [], "context": {}}
            
            response = client.get("/api/knowledge-graph")
            assert response.status_code == 200
            data = response.json()
            assert "nodes" in data
            assert "edges" in data
    
    def test_get_knowledge_graph_with_domain(self, client, sample_domain):
        """Test getting knowledge graph filtered by domain"""
        with patch('main.knowledge_graph_service.get_knowledge_graph_data') as mock_get:
            mock_get.return_value = {"nodes": [], "edges": [], "context": {"domain": "Test"}}
            
            response = client.get(f"/api/knowledge-graph?domain_id={sample_domain.id}")
            assert response.status_code == 200
    
    def test_get_knowledge_graph_with_kp(self, client, sample_knowledge_point):
        """Test getting knowledge graph filtered by KP"""
        with patch('main.knowledge_graph_service.get_knowledge_graph_data') as mock_get:
            mock_get.return_value = {"nodes": [], "edges": [], "context": {"knowledge_point": "Test"}}
            
            response = client.get(f"/api/knowledge-graph?knowledge_point_id={sample_knowledge_point.id}")
            assert response.status_code == 200
    
    def test_get_knowledge_graph_both_filters_error(self, client, sample_domain, sample_knowledge_point):
        """Test getting knowledge graph with both filters fails"""
        response = client.get(
            f"/api/knowledge-graph?domain_id={sample_domain.id}&knowledge_point_id={sample_knowledge_point.id}"
        )
        assert response.status_code == 400
        assert "only one filter" in response.json()["detail"].lower()


class TestAnalyzeUrlEndpoint:
    """Tests for URL analysis endpoint"""
    
    def test_analyze_url_new_article(self, client):
        """Test analyzing a new URL"""
        with patch('main.content_extractor.extract_content') as mock_extract:
            mock_extract.return_value = {"title": "New Page", "content": "Page content"}
            
            with patch('main.llm_service.analyze_article') as mock_analyze:
                mock_analyze.return_value = {"domains": ["Tech"], "knowledge_points": ["Python"]}
                
                response = client.post("/api/articles/analyze-url?url=https://example.com/new-page")
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "created"
                assert "article_id" in data
    
    def test_analyze_url_existing_article(self, client, sample_article):
        """Test analyzing an existing URL returns exists status"""
        with patch('main.content_extractor.extract_content') as mock_extract:
            mock_extract.return_value = {"title": "Existing", "content": "Content"}
            
            with patch('main.llm_service.analyze_article') as mock_analyze:
                mock_analyze.return_value = {"domains": [], "knowledge_points": []}
                
                response = client.post(f"/api/articles/analyze-url?url={sample_article.url}")
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "exists"


class TestSyncEndpoint:
    """Tests for sync pipeline endpoint"""
    
    def test_full_sync_article_not_found(self, client):
        """Test sync for non-existent article"""
        response = client.post("/api/sync/full-pipeline?article_id=999")
        assert response.status_code == 404
    
    def test_full_sync_success(self, client, sample_article):
        """Test successful sync"""
        # Mock the sync services
        with patch('main.neo4j_sync', None), \
             patch('main.notion_sync', None), \
             patch('main.obsidian_sync', None):
            
            response = client.post(f"/api/sync/full-pipeline?article_id={sample_article.id}")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "synced"
            assert data["article_id"] == sample_article.id
    
    def test_full_sync_with_neo4j(self, client, sample_article):
        """Test sync with Neo4j service enabled"""
        mock_neo4j = MagicMock()
        mock_neo4j.sync_article.return_value = "neo4j-new-id"
        
        with patch('main.neo4j_sync', mock_neo4j), \
             patch('main.notion_sync', None), \
             patch('main.obsidian_sync', None):
            
            response = client.post(f"/api/sync/full-pipeline?article_id={sample_article.id}")
            assert response.status_code == 200
            data = response.json()
            assert data["neo4j_id"] == "neo4j-new-id"
    
    def test_full_sync_with_notion(self, client, sample_article):
        """Test sync with Notion service enabled"""
        mock_notion = MagicMock()
        mock_notion.push_bookmark_inbox.return_value = "notion-page-id"
        
        with patch('main.neo4j_sync', None), \
             patch('main.notion_sync', mock_notion), \
             patch('main.obsidian_sync', None):
            
            response = client.post(f"/api/sync/full-pipeline?article_id={sample_article.id}")
            assert response.status_code == 200
            data = response.json()
            assert data["notion_page_id"] == "notion-page-id"
    
    def test_full_sync_with_obsidian(self, client, sample_article):
        """Test sync with Obsidian service enabled"""
        mock_obsidian = MagicMock()
        mock_obsidian.export_article.return_value = "/path/to/markdown.md"
        
        with patch('main.neo4j_sync', None), \
             patch('main.notion_sync', None), \
             patch('main.obsidian_sync', mock_obsidian):
            
            response = client.post(f"/api/sync/full-pipeline?article_id={sample_article.id}")
            assert response.status_code == 200
            data = response.json()
            assert data["markdown_path"] == "/path/to/markdown.md"
    
    def test_full_sync_notion_error(self, client, sample_article):
        """Test sync handles Notion error gracefully"""
        mock_notion = MagicMock()
        mock_notion.push_bookmark_inbox.side_effect = RuntimeError("Notion API error")
        
        with patch('main.neo4j_sync', None), \
             patch('main.notion_sync', mock_notion), \
             patch('main.obsidian_sync', None):
            
            response = client.post(f"/api/sync/full-pipeline?article_id={sample_article.id}")
            assert response.status_code == 200  # Should not fail
    
    def test_full_sync_obsidian_error(self, client, sample_article):
        """Test sync handles Obsidian error gracefully"""
        mock_obsidian = MagicMock()
        mock_obsidian.export_article.side_effect = Exception("Export failed")
        
        with patch('main.neo4j_sync', None), \
             patch('main.notion_sync', None), \
             patch('main.obsidian_sync', mock_obsidian):
            
            response = client.post(f"/api/sync/full-pipeline?article_id={sample_article.id}")
            assert response.status_code == 200  # Should not fail


class TestStartupShutdown:
    """Tests for app startup and shutdown events"""
    
    def test_startup_event_neo4j_disabled(self, client):
        """Test startup event handles Neo4j disabled gracefully"""
        # The test client already initializes the app
        # Just verify the app works without Neo4j
        response = client.get("/")
        assert response.status_code == 200
    
    def test_startup_event_with_env_vars(self, client):
        """Test startup event reads environment variables"""
        # App should be running and healthy
        response = client.get("/api/health")
        assert response.status_code == 200
