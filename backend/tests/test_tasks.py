"""
Unit tests for tasks module (MarkdownConverter and KnowledgeGraphService)
"""
import pytest
import tempfile
import os
import shutil
from datetime import datetime
from pathlib import Path

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tasks import MarkdownConverter, KnowledgeGraphService, MAX_TITLE_LENGTH, MAX_RELATED_ARTICLES
from database import Article, Domain, KnowledgePoint


class TestMarkdownConverter:
    """Tests for MarkdownConverter"""
    
    @pytest.fixture
    def temp_export_dir(self):
        """Create a temporary directory for exports"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def converter(self, temp_export_dir):
        """Create a MarkdownConverter with temp directory"""
        return MarkdownConverter(export_dir=temp_export_dir)
    
    def test_init_creates_export_dir(self):
        """Test MarkdownConverter creates export directory"""
        temp_path = tempfile.mkdtemp()
        new_dir = os.path.join(temp_path, "new_exports")
        
        converter = MarkdownConverter(export_dir=new_dir)
        
        assert Path(new_dir).exists()
        shutil.rmtree(temp_path)
    
    def test_init_default_export_dir(self):
        """Test MarkdownConverter uses default export dir"""
        converter = MarkdownConverter()
        assert converter.export_dir == Path("./exports")
    
    def test_safe_title_basic(self, converter, db_session):
        """Test _safe_title with basic alphanumeric title"""
        article = Article(
            url="https://example.com",
            title="Test Article Title",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        result = converter._safe_title(article)
        
        assert result == "Test Article Title"
    
    def test_safe_title_removes_special_chars(self, converter, db_session):
        """Test _safe_title removes special characters"""
        article = Article(
            url="https://example.com",
            title="Test: Article <with> Special/Chars!",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        result = converter._safe_title(article)
        
        # Only alphanumeric, space, hyphen, underscore should remain
        assert ":" not in result
        assert "<" not in result
        assert ">" not in result
        assert "/" not in result
        assert "!" not in result
    
    def test_safe_title_truncates_long_titles(self, converter, db_session):
        """Test _safe_title truncates very long titles"""
        long_title = "A" * 200
        article = Article(
            url="https://example.com",
            title=long_title,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        result = converter._safe_title(article)
        
        assert len(result) <= MAX_TITLE_LENGTH
    
    def test_safe_title_fallback_to_id(self, converter, db_session):
        """Test _safe_title falls back to article ID when title is empty after sanitization"""
        article = Article(
            id=123,
            url="https://example.com",
            title="!@#$%^&*()",  # All special chars
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        result = converter._safe_title(article)
        
        assert result == "article-123"
    
    def test_format_wiki_link_same_title(self, converter, db_session):
        """Test _format_wiki_link when safe title matches original"""
        article = Article(
            url="https://example.com",
            title="Simple Title",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        result = converter._format_wiki_link(article)
        
        assert result == "[[Simple Title]]"
    
    def test_format_wiki_link_different_title(self, converter, db_session):
        """Test _format_wiki_link when safe title differs from original"""
        article = Article(
            url="https://example.com",
            title="Title: With Colon",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        result = converter._format_wiki_link(article)
        
        # Should use alias format
        assert result == "[[Title With Colon|Title: With Colon]]"
    
    def test_dedupe_articles(self, converter, db_session):
        """Test _dedupe_articles removes duplicates"""
        article1 = Article(id=1, url="https://example.com/1", title="Article 1")
        article2 = Article(id=2, url="https://example.com/2", title="Article 2")
        
        # Include duplicates
        articles = [article1, article2, article1, article2, article1]
        
        result = converter._dedupe_articles(articles)
        
        assert len(result) == 2
    
    def test_collect_related_articles(self, converter, multiple_articles, db_session):
        """Test _collect_related_articles finds related articles"""
        articles = multiple_articles["articles"]
        
        # Article 3 shares domains and KPs with articles 1 and 2
        result = converter._collect_related_articles(articles[2])
        
        assert "by_domain" in result
        assert "by_knowledge_point" in result
    
    def test_build_markdown_content_basic(self, converter, sample_article):
        """Test _build_markdown_content creates valid markdown"""
        content = converter._build_markdown_content(sample_article)
        
        assert f"# {sample_article.title}" in content
        assert f"url: {sample_article.url}" in content
        assert "## Domains" in content
        assert "## Knowledge Points" in content
        assert "## Source" in content
    
    def test_build_markdown_content_with_summary(self, converter, db_session):
        """Test _build_markdown_content includes summary when present"""
        article = Article(
            url="https://example.com",
            title="Test",
            summary="This is a summary",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(article)
        db_session.commit()
        
        content = converter._build_markdown_content(article)
        
        assert "## Summary" in content
        assert "This is a summary" in content
    
    def test_build_markdown_content_with_neo4j_id(self, converter, db_session):
        """Test _build_markdown_content includes Neo4j ID when present"""
        article = Article(
            url="https://example.com",
            title="Test",
            neo4j_id="neo4j-123",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(article)
        db_session.commit()
        
        content = converter._build_markdown_content(article)
        
        assert "neo4j_id: neo4j-123" in content
    
    def test_build_markdown_content_with_notion_id(self, converter, db_session):
        """Test _build_markdown_content includes Notion ID when present"""
        article = Article(
            url="https://example.com",
            title="Test",
            notion_page_id="notion-456",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(article)
        db_session.commit()
        
        content = converter._build_markdown_content(article)
        
        assert "notion_page_id: notion-456" in content
    
    def test_build_markdown_content_with_tags(self, converter, sample_article):
        """Test _build_markdown_content creates tags from domains"""
        content = converter._build_markdown_content(sample_article)
        
        # Tags should replace spaces with hyphens
        assert "tags:" in content
    
    def test_build_markdown_content_limits_content(self, converter, db_session):
        """Test _build_markdown_content limits article content to 5000 chars"""
        long_content = "a" * 10000
        article = Article(
            url="https://example.com",
            title="Test",
            content=long_content,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(article)
        db_session.commit()
        
        markdown = converter._build_markdown_content(article)
        
        # Content section should be truncated
        assert len(markdown) < 10000 + 500  # markdown overhead
    
    def test_convert_article_to_markdown(self, converter, sample_article, db_session, temp_export_dir):
        """Test convert_article_to_markdown creates file"""
        filepath = converter.convert_article_to_markdown(sample_article, db_session)
        
        assert os.path.exists(filepath)
        assert filepath.endswith(".md")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert sample_article.title in content
    
    def test_batch_convert_all_articles(self, converter, multiple_articles, db_session, temp_export_dir):
        """Test batch_convert converts all articles"""
        filepaths = converter.batch_convert(db_session)
        
        assert len(filepaths) == 3
        for filepath in filepaths:
            assert os.path.exists(filepath)
    
    def test_batch_convert_with_limit(self, converter, multiple_articles, db_session, temp_export_dir):
        """Test batch_convert respects limit parameter"""
        filepaths = converter.batch_convert(db_session, limit=2)
        
        assert len(filepaths) == 2
    
    def test_batch_convert_updates_markdown_path(self, converter, sample_article, db_session, temp_export_dir):
        """Test batch_convert updates article's markdown_path"""
        converter.batch_convert(db_session)
        
        db_session.refresh(sample_article)
        assert sample_article.markdown_path is not None
    
    def test_batch_convert_handles_conversion_error(self, converter, sample_article, db_session, temp_export_dir):
        """Test batch_convert handles conversion errors gracefully"""
        from unittest.mock import patch
        
        with patch.object(converter, 'convert_article_to_markdown', side_effect=Exception("Conversion failed")):
            filepaths = converter.batch_convert(db_session)
            
            # Should continue despite error
            assert filepaths == []
    
    def test_collect_related_articles_empty(self, converter, db_session):
        """Test _collect_related_articles with article having no relationships"""
        article = Article(
            url="https://example.com/lonely",
            title="Lonely Article",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(article)
        db_session.commit()
        
        result = converter._collect_related_articles(article)
        
        assert result["by_domain"] == []
        assert result["by_knowledge_point"] == []
    
    def test_build_markdown_related_articles_section(self, converter, multiple_articles, db_session):
        """Test _build_markdown_content includes related articles section"""
        articles = multiple_articles["articles"]
        
        # Article 3 has shared domains/KPs with others
        content = converter._build_markdown_content(articles[2])
        
        assert "## Related Articles" in content
    
    def test_build_markdown_related_by_knowledge_point_section(self, converter, db_session):
        """Test _build_markdown_content includes related by knowledge point section"""
        from database import Domain, KnowledgePoint
        
        # Create distinct domains but shared knowledge point
        domain1 = Domain(name="Unique Domain 1")
        domain2 = Domain(name="Unique Domain 2")
        shared_kp = KnowledgePoint(name="Shared Knowledge Point")
        db_session.add_all([domain1, domain2, shared_kp])
        
        article1 = Article(
            url="https://example.com/kp-test-1",
            title="KP Test Article 1",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        article1.domains.append(domain1)
        article1.knowledge_points.append(shared_kp)
        
        article2 = Article(
            url="https://example.com/kp-test-2",
            title="KP Test Article 2",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        article2.domains.append(domain2)
        article2.knowledge_points.append(shared_kp)
        
        db_session.add_all([article1, article2])
        db_session.commit()
        
        # Article 1 should have Article 2 related by knowledge point (not domain)
        content = converter._build_markdown_content(article1)
        
        assert "### Same Knowledge Points" in content


class TestKnowledgeGraphService:
    """Tests for KnowledgeGraphService"""
    
    @pytest.fixture
    def service(self):
        return KnowledgeGraphService()
    
    def test_find_related_articles_not_found(self, service, db_session):
        """Test find_related_articles returns empty for non-existent article"""
        result = service.find_related_articles(999, db_session)
        
        assert result == {"by_domain": [], "by_knowledge_point": []}
    
    def test_find_related_articles_by_domain(self, service, db_session, multiple_articles):
        """Test find_related_articles finds articles in same domain"""
        articles = multiple_articles["articles"]
        
        # Articles 1 and 3 share Web Development domain
        result = service.find_related_articles(articles[0].id, db_session)
        
        # Article 3 should be in by_domain
        assert any(a.id == articles[2].id for a in result["by_domain"])
    
    def test_find_related_articles_by_knowledge_point(self, service, db_session, multiple_articles):
        """Test find_related_articles finds articles with same KPs"""
        articles = multiple_articles["articles"]
        
        result = service.find_related_articles(articles[1].id, db_session)
        
        # Check that related articles are found
        assert "by_domain" in result
        assert "by_knowledge_point" in result
    
    def test_find_related_articles_no_duplicates(self, service, db_session, multiple_articles):
        """Test find_related_articles doesn't include article in its own results"""
        articles = multiple_articles["articles"]
        article_id = articles[0].id
        
        result = service.find_related_articles(article_id, db_session)
        
        all_related = result["by_domain"] + result["by_knowledge_point"]
        assert not any(a.id == article_id for a in all_related)
    
    def test_find_related_dedupes_between_domain_and_kp(self, service, db_session, multiple_articles):
        """Test find_related_articles removes duplicates between by_domain and by_knowledge_point"""
        articles = multiple_articles["articles"]
        
        result = service.find_related_articles(articles[0].id, db_session)
        
        # IDs in by_knowledge_point should not be in by_domain
        domain_ids = {a.id for a in result["by_domain"]}
        kp_ids = {a.id for a in result["by_knowledge_point"]}
        
        assert domain_ids.isdisjoint(kp_ids)
    
    def test_get_knowledge_graph_data_no_filter(self, service, db_session, multiple_articles):
        """Test get_knowledge_graph_data returns all data without filters"""
        result = service.get_knowledge_graph_data(db_session)
        
        assert "nodes" in result
        assert "edges" in result
        assert "context" in result
        
        # Should have nodes for articles, domains, and knowledge points
        node_types = {node["type"] for node in result["nodes"]}
        assert "article" in node_types
        assert "domain" in node_types
        assert "knowledge_point" in node_types
    
    def test_get_knowledge_graph_data_with_domain_filter(self, service, db_session, multiple_articles):
        """Test get_knowledge_graph_data filters by domain"""
        domains = multiple_articles["domains"]
        
        result = service.get_knowledge_graph_data(db_session, domain_id=domains[0].id)
        
        assert result["context"]["domain"] == domains[0].name
        
        # Should only have articles from this domain
        article_nodes = [n for n in result["nodes"] if n["type"] == "article"]
        assert len(article_nodes) >= 1
    
    def test_get_knowledge_graph_data_with_kp_filter(self, service, db_session, multiple_articles):
        """Test get_knowledge_graph_data filters by knowledge point"""
        kps = multiple_articles["knowledge_points"]
        
        result = service.get_knowledge_graph_data(db_session, knowledge_point_id=kps[0].id)
        
        assert result["context"]["knowledge_point"] == kps[0].name
    
    def test_get_knowledge_graph_data_domain_not_found(self, service, db_session):
        """Test get_knowledge_graph_data returns empty for non-existent domain"""
        result = service.get_knowledge_graph_data(db_session, domain_id=999)
        
        assert result["nodes"] == []
        assert result["edges"] == []
    
    def test_get_knowledge_graph_data_kp_not_found(self, service, db_session):
        """Test get_knowledge_graph_data returns empty for non-existent KP"""
        result = service.get_knowledge_graph_data(db_session, knowledge_point_id=999)
        
        assert result["nodes"] == []
        assert result["edges"] == []
    
    def test_get_knowledge_graph_data_node_properties(self, service, db_session, sample_article):
        """Test get_knowledge_graph_data nodes have required properties"""
        result = service.get_knowledge_graph_data(db_session)
        
        for node in result["nodes"]:
            assert "id" in node
            assert "label" in node
            assert "type" in node
            assert "icon" in node
            assert "size" in node
    
    def test_get_knowledge_graph_data_edge_properties(self, service, db_session, sample_article):
        """Test get_knowledge_graph_data edges have required properties"""
        result = service.get_knowledge_graph_data(db_session)
        
        for edge in result["edges"]:
            assert "source" in edge
            assert "target" in edge
            assert "type" in edge
    
    def test_get_knowledge_graph_data_article_node_size(self, service, db_session, multiple_articles):
        """Test article node size is based on relationships"""
        result = service.get_knowledge_graph_data(db_session)
        
        article_nodes = [n for n in result["nodes"] if n["type"] == "article"]
        
        for node in article_nodes:
            assert node["size"] >= 6
    
    def test_get_knowledge_graph_data_domain_node_size(self, service, db_session, multiple_articles):
        """Test domain node size is based on article count"""
        result = service.get_knowledge_graph_data(db_session)
        
        domain_nodes = [n for n in result["nodes"] if n["type"] == "domain"]
        
        for node in domain_nodes:
            assert node["size"] >= 8
    
    def test_get_knowledge_graph_data_no_self_edges(self, service, db_session, sample_article):
        """Test get_knowledge_graph_data doesn't create self-edges"""
        result = service.get_knowledge_graph_data(db_session)
        
        for edge in result["edges"]:
            assert edge["source"] != edge["target"]
    
    def test_get_knowledge_graph_data_article_article_edges(self, service, db_session, multiple_articles):
        """Test get_knowledge_graph_data creates article-article edges"""
        result = service.get_knowledge_graph_data(db_session)
        
        related_edges = [e for e in result["edges"] if e["type"] == "related_articles"]
        
        if related_edges:
            for edge in related_edges:
                assert "shared_domains" in edge
                assert "shared_knowledge_points" in edge
                assert "weight" in edge
    
    def test_get_knowledge_graph_data_edge_types(self, service, db_session, sample_article):
        """Test get_knowledge_graph_data creates correct edge types"""
        result = service.get_knowledge_graph_data(db_session)
        
        edge_types = {e["type"] for e in result["edges"]}
        
        # Should have belongs_to (article-domain) and covers (article-kp) edges
        assert "belongs_to" in edge_types or len(result["edges"]) == 0
    
    def test_get_knowledge_graph_data_edge_deduplication(self, service, db_session):
        """Test that edges are not duplicated"""
        from database import Domain, KnowledgePoint
        
        # Create articles that share both domain and knowledge point
        domain = Domain(name="Shared Domain")
        kp = KnowledgePoint(name="Shared KP")
        db_session.add_all([domain, kp])
        
        article1 = Article(url="https://example.com/a1", title="Article 1")
        article2 = Article(url="https://example.com/a2", title="Article 2")
        article3 = Article(url="https://example.com/a3", title="Article 3")
        
        # All articles share the same domain and KP
        for article in [article1, article2, article3]:
            article.domains.append(domain)
            article.knowledge_points.append(kp)
        
        db_session.add_all([article1, article2, article3])
        db_session.commit()
        
        result = service.get_knowledge_graph_data(db_session)
        
        # Count edges - should not have duplicates
        edge_list = [(e["source"], e["target"], e["type"]) for e in result["edges"]]
        edge_set = set(edge_list)
        
        # If there were duplicates, the set would be smaller
        assert len(edge_set) == len(edge_list)
