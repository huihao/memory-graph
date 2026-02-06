"""
Unit tests for Pydantic schemas
"""
import pytest
from datetime import datetime
from pydantic import ValidationError

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from schemas import (
    DomainBase, DomainCreate, Domain,
    KnowledgePointBase, KnowledgePointCreate, KnowledgePoint,
    ArticleBase, ArticleCreate, Article,
    ArticleList, SearchResult, DomainStats, Stats
)


class TestDomainSchemas:
    """Tests for Domain-related schemas"""
    
    def test_domain_base_with_name(self):
        """Test DomainBase with required name"""
        domain = DomainBase(name="Technology")
        assert domain.name == "Technology"
        assert domain.description is None
    
    def test_domain_base_with_description(self):
        """Test DomainBase with optional description"""
        domain = DomainBase(name="Technology", description="Tech articles")
        assert domain.name == "Technology"
        assert domain.description == "Tech articles"
    
    def test_domain_base_missing_name(self):
        """Test DomainBase requires name"""
        with pytest.raises(ValidationError):
            DomainBase()
    
    def test_domain_create(self):
        """Test DomainCreate schema"""
        domain = DomainCreate(name="New Domain")
        assert domain.name == "New Domain"
    
    def test_domain_full(self):
        """Test full Domain schema with all fields"""
        now = datetime.utcnow()
        domain = Domain(
            id=1,
            name="Test Domain",
            description="Description",
            created_at=now
        )
        assert domain.id == 1
        assert domain.name == "Test Domain"
        assert domain.created_at == now


class TestKnowledgePointSchemas:
    """Tests for KnowledgePoint-related schemas"""
    
    def test_knowledge_point_base_with_name(self):
        """Test KnowledgePointBase with required name"""
        kp = KnowledgePointBase(name="Python")
        assert kp.name == "Python"
        assert kp.description is None
    
    def test_knowledge_point_base_with_description(self):
        """Test KnowledgePointBase with optional description"""
        kp = KnowledgePointBase(name="Python", description="Python programming")
        assert kp.name == "Python"
        assert kp.description == "Python programming"
    
    def test_knowledge_point_base_missing_name(self):
        """Test KnowledgePointBase requires name"""
        with pytest.raises(ValidationError):
            KnowledgePointBase()
    
    def test_knowledge_point_create(self):
        """Test KnowledgePointCreate schema"""
        kp = KnowledgePointCreate(name="New KP")
        assert kp.name == "New KP"
    
    def test_knowledge_point_full(self):
        """Test full KnowledgePoint schema with all fields"""
        now = datetime.utcnow()
        kp = KnowledgePoint(
            id=1,
            name="Test KP",
            description="Description",
            created_at=now
        )
        assert kp.id == 1
        assert kp.name == "Test KP"
        assert kp.created_at == now


class TestArticleSchemas:
    """Tests for Article-related schemas"""
    
    def test_article_base_required_fields(self):
        """Test ArticleBase with required fields only"""
        article = ArticleBase(
            url="https://example.com",
            title="Test Title"
        )
        assert article.url == "https://example.com"
        assert article.title == "Test Title"
        assert article.content is None
        assert article.summary is None
    
    def test_article_base_all_fields(self):
        """Test ArticleBase with all fields"""
        article = ArticleBase(
            url="https://example.com",
            title="Test Title",
            content="Test content",
            summary="Test summary"
        )
        assert article.url == "https://example.com"
        assert article.title == "Test Title"
        assert article.content == "Test content"
        assert article.summary == "Test summary"
    
    def test_article_base_missing_url(self):
        """Test ArticleBase requires url"""
        with pytest.raises(ValidationError):
            ArticleBase(title="Test")
    
    def test_article_base_missing_title(self):
        """Test ArticleBase requires title"""
        with pytest.raises(ValidationError):
            ArticleBase(url="https://example.com")
    
    def test_article_create_with_names(self):
        """Test ArticleCreate with domain and knowledge point names"""
        article = ArticleCreate(
            url="https://example.com",
            title="Test Title",
            domain_names=["ML", "AI"],
            knowledge_point_names=["Python", "TensorFlow"]
        )
        assert article.domain_names == ["ML", "AI"]
        assert article.knowledge_point_names == ["Python", "TensorFlow"]
    
    def test_article_create_default_empty_lists(self):
        """Test ArticleCreate defaults to empty lists"""
        article = ArticleCreate(
            url="https://example.com",
            title="Test Title"
        )
        assert article.domain_names == []
        assert article.knowledge_point_names == []
    
    def test_article_full(self):
        """Test full Article schema with all fields"""
        now = datetime.utcnow()
        domain = Domain(id=1, name="Domain", created_at=now)
        kp = KnowledgePoint(id=1, name="KP", created_at=now)
        
        article = Article(
            id=1,
            url="https://example.com",
            title="Test Title",
            content="Content",
            summary="Summary",
            created_at=now,
            updated_at=now,
            markdown_path="/path/to/file.md",
            neo4j_id="neo4j-123",
            notion_page_id="notion-456",
            domains=[domain],
            knowledge_points=[kp]
        )
        
        assert article.id == 1
        assert article.markdown_path == "/path/to/file.md"
        assert article.neo4j_id == "neo4j-123"
        assert article.notion_page_id == "notion-456"
        assert len(article.domains) == 1
        assert len(article.knowledge_points) == 1
    
    def test_article_default_empty_relationships(self):
        """Test Article defaults to empty lists for relationships"""
        now = datetime.utcnow()
        article = Article(
            id=1,
            url="https://example.com",
            title="Test",
            created_at=now,
            updated_at=now
        )
        assert article.domains == []
        assert article.knowledge_points == []


class TestArticleListSchema:
    """Tests for ArticleList schema"""
    
    def test_article_list_empty(self):
        """Test ArticleList with empty articles"""
        result = ArticleList(articles=[], total=0)
        assert result.articles == []
        assert result.total == 0
    
    def test_article_list_with_articles(self):
        """Test ArticleList with articles"""
        now = datetime.utcnow()
        article = Article(
            id=1,
            url="https://example.com",
            title="Test",
            created_at=now,
            updated_at=now
        )
        result = ArticleList(articles=[article], total=1)
        assert len(result.articles) == 1
        assert result.total == 1


class TestSearchResultSchema:
    """Tests for SearchResult schema"""
    
    def test_search_result_empty(self):
        """Test SearchResult with no results"""
        result = SearchResult(
            articles=[],
            total=0,
            skip=0,
            limit=20,
            has_more=False
        )
        assert result.articles == []
        assert result.total == 0
        assert result.has_more is False
    
    def test_search_result_with_pagination(self):
        """Test SearchResult with pagination info"""
        now = datetime.utcnow()
        article = Article(
            id=1,
            url="https://example.com",
            title="Test",
            created_at=now,
            updated_at=now
        )
        result = SearchResult(
            articles=[article],
            total=100,
            skip=20,
            limit=20,
            has_more=True
        )
        assert result.total == 100
        assert result.skip == 20
        assert result.limit == 20
        assert result.has_more is True


class TestStatsSchemas:
    """Tests for Stats-related schemas"""
    
    def test_domain_stats(self):
        """Test DomainStats schema"""
        stats = DomainStats(id=1, name="Technology", article_count=10)
        assert stats.id == 1
        assert stats.name == "Technology"
        assert stats.article_count == 10
    
    def test_stats_full(self):
        """Test full Stats schema"""
        domain_stats = DomainStats(id=1, name="Technology", article_count=10)
        stats = Stats(
            total_articles=100,
            total_domains=5,
            total_knowledge_points=20,
            recent_articles=15,
            top_domains=[domain_stats]
        )
        assert stats.total_articles == 100
        assert stats.total_domains == 5
        assert stats.total_knowledge_points == 20
        assert stats.recent_articles == 15
        assert len(stats.top_domains) == 1
    
    def test_stats_empty_top_domains(self):
        """Test Stats with empty top_domains"""
        stats = Stats(
            total_articles=0,
            total_domains=0,
            total_knowledge_points=0,
            recent_articles=0,
            top_domains=[]
        )
        assert stats.top_domains == []


class TestSchemaValidation:
    """Tests for schema validation edge cases"""
    
    def test_domain_empty_name(self):
        """Test Domain with empty string name (should be allowed by Pydantic)"""
        domain = DomainBase(name="")
        assert domain.name == ""
    
    def test_article_url_any_string(self):
        """Test that url is just a string (not validated as URL)"""
        article = ArticleBase(url="not-a-url", title="Test")
        assert article.url == "not-a-url"
    
    def test_article_long_content(self):
        """Test Article with very long content"""
        long_content = "a" * 100000
        article = ArticleBase(
            url="https://example.com",
            title="Test",
            content=long_content
        )
        assert len(article.content) == 100000
    
    def test_article_special_characters_in_title(self):
        """Test Article with special characters in title"""
        article = ArticleBase(
            url="https://example.com",
            title="Test <script>alert('xss')</script>"
        )
        assert "<script>" in article.title
