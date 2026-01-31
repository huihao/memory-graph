"""
Unit tests for integration modules (Neo4j, Notion, Obsidian sync)
"""
import pytest
from unittest.mock import patch, MagicMock
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'integration'))

from integration.neo4j_sync import Neo4jSync
from integration.notion_sync import NotionSync
from integration.obsidian_sync import ObsidianSync
from database import Article


class TestNeo4jSync:
    """Tests for Neo4jSync"""
    
    def test_init_without_password_raises(self):
        """Test Neo4jSync raises ValueError without password"""
        with pytest.raises(ValueError) as exc_info:
            Neo4jSync("bolt://localhost:7687", "neo4j", "")
        
        assert "NEO4J_PASSWORD" in str(exc_info.value)
    
    def test_init_with_password(self):
        """Test Neo4jSync initializes with password"""
        with patch('integration.neo4j_sync.GraphDatabase.driver') as mock_driver:
            sync = Neo4jSync("bolt://localhost:7687", "neo4j", "password123")
            
            mock_driver.assert_called_once_with(
                "bolt://localhost:7687",
                auth=("neo4j", "password123")
            )
    
    def test_close(self):
        """Test Neo4jSync close method"""
        with patch('integration.neo4j_sync.GraphDatabase.driver') as mock_driver_class:
            mock_driver = MagicMock()
            mock_driver_class.return_value = mock_driver
            
            sync = Neo4jSync("bolt://localhost:7687", "neo4j", "password")
            sync.close()
            
            mock_driver.close.assert_called_once()
    
    def test_sync_article_new(self):
        """Test syncing a new article (no existing neo4j_id)"""
        with patch('integration.neo4j_sync.GraphDatabase.driver') as mock_driver_class:
            mock_driver = MagicMock()
            mock_session = MagicMock()
            mock_result = MagicMock()
            mock_result.single.return_value = {"neo4j_id": "bookmark-abc123"}
            
            mock_driver.session.return_value.__enter__ = MagicMock(return_value=mock_session)
            mock_driver.session.return_value.__exit__ = MagicMock(return_value=None)
            mock_session.run.return_value = mock_result
            mock_driver_class.return_value = mock_driver
            
            sync = Neo4jSync("bolt://localhost:7687", "neo4j", "password")
            
            article = {
                "url": "https://example.com",
                "title": "Test Article"
            }
            
            result = sync.sync_article(article)
            
            assert result == "bookmark-abc123"
            mock_session.run.assert_called_once()
    
    def test_sync_article_existing(self):
        """Test syncing an existing article (with neo4j_id)"""
        with patch('integration.neo4j_sync.GraphDatabase.driver') as mock_driver_class:
            mock_driver = MagicMock()
            mock_session = MagicMock()
            mock_result = MagicMock()
            mock_result.single.return_value = {"neo4j_id": "existing-id"}
            
            mock_driver.session.return_value.__enter__ = MagicMock(return_value=mock_session)
            mock_driver.session.return_value.__exit__ = MagicMock(return_value=None)
            mock_session.run.return_value = mock_result
            mock_driver_class.return_value = mock_driver
            
            sync = Neo4jSync("bolt://localhost:7687", "neo4j", "password")
            
            article = {
                "url": "https://example.com",
                "title": "Test Article"
            }
            
            result = sync.sync_article(article, neo4j_id="existing-id")
            
            assert result == "existing-id"
    
    def test_sync_article_with_optional_fields(self):
        """Test syncing article with optional fields"""
        with patch('integration.neo4j_sync.GraphDatabase.driver') as mock_driver_class:
            mock_driver = MagicMock()
            mock_session = MagicMock()
            mock_result = MagicMock()
            mock_result.single.return_value = {"neo4j_id": "bookmark-123"}
            
            mock_driver.session.return_value.__enter__ = MagicMock(return_value=mock_session)
            mock_driver.session.return_value.__exit__ = MagicMock(return_value=None)
            mock_session.run.return_value = mock_result
            mock_driver_class.return_value = mock_driver
            
            sync = Neo4jSync("bolt://localhost:7687", "neo4j", "password")
            
            article = {
                "url": "https://example.com",
                "title": "Test Article",
                "markdown_path": "/path/to/file.md",
                "notion_page_id": "notion-123"
            }
            
            result = sync.sync_article(article)
            
            assert result == "bookmark-123"
            call_kwargs = mock_session.run.call_args
            assert "obsidian_path" in call_kwargs[1] or "/path/to/file.md" in str(call_kwargs)


class TestNotionSync:
    """Tests for NotionSync"""
    
    def test_init(self):
        """Test NotionSync initialization"""
        sync = NotionSync("api-key", "database-id")
        
        assert sync.api_key == "api-key"
        assert sync.database_id == "database-id"
    
    def test_push_bookmark_no_config(self):
        """Test push_bookmark_inbox returns None when not configured"""
        sync = NotionSync("", "")
        
        result = sync.push_bookmark_inbox({"title": "Test", "url": "https://example.com"}, None)
        
        assert result is None
    
    def test_push_bookmark_success(self):
        """Test successful bookmark push"""
        with patch('integration.notion_sync.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {"id": "notion-page-123"}
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response
            
            sync = NotionSync("api-key", "database-id")
            
            article = {
                "title": "Test Article",
                "url": "https://example.com",
                "domains": ["Tech", "AI"]
            }
            
            result = sync.push_bookmark_inbox(article, None)
            
            assert result == "notion-page-123"
            mock_post.assert_called_once()
    
    def test_push_bookmark_with_neo4j_id(self):
        """Test bookmark push includes Neo4j ID when provided"""
        with patch('integration.notion_sync.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {"id": "notion-page-123"}
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response
            
            sync = NotionSync("api-key", "database-id")
            
            article = {
                "title": "Test Article",
                "url": "https://example.com"
            }
            
            result = sync.push_bookmark_inbox(article, "neo4j-123")
            
            assert result == "notion-page-123"
            call_kwargs = mock_post.call_args
            payload = call_kwargs[1]["json"]
            assert "Neo4j ID" in payload["properties"]
    
    def test_push_bookmark_no_domains(self):
        """Test bookmark push with no domains"""
        with patch('integration.notion_sync.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {"id": "notion-page-123"}
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response
            
            sync = NotionSync("api-key", "database-id")
            
            article = {
                "title": "Test Article",
                "url": "https://example.com"
            }
            
            result = sync.push_bookmark_inbox(article, None)
            
            assert result == "notion-page-123"
    
    def test_push_bookmark_request_error(self):
        """Test bookmark push raises RuntimeError on request failure"""
        import requests
        
        with patch('integration.notion_sync.requests.post') as mock_post:
            mock_post.side_effect = requests.RequestException("Network error")
            
            sync = NotionSync("api-key", "database-id")
            
            article = {
                "title": "Test Article",
                "url": "https://example.com"
            }
            
            with pytest.raises(RuntimeError) as exc_info:
                sync.push_bookmark_inbox(article, None)
            
            assert "Notion sync failed" in str(exc_info.value)
    
    def test_push_bookmark_headers(self):
        """Test bookmark push uses correct headers"""
        with patch('integration.notion_sync.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {"id": "notion-page-123"}
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response
            
            sync = NotionSync("my-api-key", "database-id")
            
            article = {
                "title": "Test",
                "url": "https://example.com"
            }
            
            sync.push_bookmark_inbox(article, None)
            
            call_kwargs = mock_post.call_args
            headers = call_kwargs[1]["headers"]
            
            assert headers["Authorization"] == "Bearer my-api-key"
            assert headers["Notion-Version"] == "2022-06-28"
            assert headers["Content-Type"] == "application/json"


class TestObsidianSync:
    """Tests for ObsidianSync"""
    
    @pytest.fixture
    def temp_vault(self):
        """Create a temporary vault directory"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_init_with_path(self, temp_vault):
        """Test ObsidianSync initialization with vault path"""
        sync = ObsidianSync(temp_vault)
        
        assert sync.vault_path == Path(temp_vault)
    
    def test_init_empty_path(self):
        """Test ObsidianSync initialization with empty path"""
        sync = ObsidianSync("")
        
        assert sync.vault_path is None
    
    def test_export_article_no_vault(self):
        """Test export_article returns None when vault not configured"""
        sync = ObsidianSync("")
        
        article = MagicMock()
        db = MagicMock()
        
        result = sync.export_article(article, db)
        
        assert result is None
    
    def test_export_article_success(self, temp_vault):
        """Test successful article export"""
        sync = ObsidianSync(temp_vault)
        
        # Create mock article
        article = MagicMock()
        article.id = 1
        article.title = "Test Article"
        article.url = "https://example.com"
        article.content = "Test content"
        article.summary = "Test summary"
        article.created_at = datetime.utcnow()
        article.updated_at = datetime.utcnow()
        article.neo4j_id = None
        article.notion_page_id = None
        article.domains = []
        article.knowledge_points = []
        
        db = MagicMock()
        
        with patch('integration.obsidian_sync.MarkdownConverter') as mock_converter_class:
            mock_converter = MagicMock()
            mock_converter.convert_article_to_markdown.return_value = "/path/to/article.md"
            mock_converter_class.return_value = mock_converter
            
            result = sync.export_article(article, db)
            
            assert result == "/path/to/article.md"
            mock_converter_class.assert_called_once_with(str(Path(temp_vault) / "drafts"))
            mock_converter.convert_article_to_markdown.assert_called_once_with(article, db)
    
    def test_export_article_creates_drafts_dir(self, temp_vault):
        """Test that export uses drafts subdirectory"""
        sync = ObsidianSync(temp_vault)
        
        article = MagicMock()
        article.id = 1
        article.title = "Test"
        article.url = "https://example.com"
        article.content = ""
        article.summary = ""
        article.created_at = datetime.utcnow()
        article.updated_at = datetime.utcnow()
        article.neo4j_id = None
        article.notion_page_id = None
        article.domains = []
        article.knowledge_points = []
        
        db = MagicMock()
        
        with patch('integration.obsidian_sync.MarkdownConverter') as mock_converter_class:
            mock_converter = MagicMock()
            mock_converter.convert_article_to_markdown.return_value = "/path/file.md"
            mock_converter_class.return_value = mock_converter
            
            sync.export_article(article, db)
            
            # Verify drafts directory is used
            expected_path = str(Path(temp_vault) / "drafts")
            mock_converter_class.assert_called_with(expected_path)


class TestIntegrationModuleImports:
    """Tests for integration module imports"""
    
    def test_neo4j_sync_import(self):
        """Test Neo4jSync can be imported"""
        from integration.neo4j_sync import Neo4jSync
        assert Neo4jSync is not None
    
    def test_notion_sync_import(self):
        """Test NotionSync can be imported"""
        from integration.notion_sync import NotionSync
        assert NotionSync is not None
    
    def test_obsidian_sync_import(self):
        """Test ObsidianSync can be imported"""
        from integration.obsidian_sync import ObsidianSync
        assert ObsidianSync is not None
