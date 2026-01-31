"""
Unit tests for database models
"""
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Base, Article, Domain, KnowledgePoint, init_db, get_db, article_domains, article_knowledge_points


class TestDatabaseModels:
    """Tests for SQLAlchemy models"""
    
    def test_article_creation(self, db_session):
        """Test creating an article"""
        article = Article(
            url="https://example.com/test",
            title="Test Article",
            content="Test content",
            summary="Test summary"
        )
        db_session.add(article)
        db_session.commit()
        
        assert article.id is not None
        assert article.url == "https://example.com/test"
        assert article.title == "Test Article"
        assert article.created_at is not None
        assert article.updated_at is not None
    
    def test_article_unique_url(self, db_session):
        """Test that article URLs must be unique"""
        article1 = Article(url="https://example.com/unique", title="Article 1")
        db_session.add(article1)
        db_session.commit()
        
        article2 = Article(url="https://example.com/unique", title="Article 2")
        db_session.add(article2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_domain_creation(self, db_session):
        """Test creating a domain"""
        domain = Domain(name="Technology", description="Tech articles")
        db_session.add(domain)
        db_session.commit()
        
        assert domain.id is not None
        assert domain.name == "Technology"
        assert domain.description == "Tech articles"
        assert domain.created_at is not None
    
    def test_domain_unique_name(self, db_session):
        """Test that domain names must be unique"""
        domain1 = Domain(name="Unique Domain")
        db_session.add(domain1)
        db_session.commit()
        
        domain2 = Domain(name="Unique Domain")
        db_session.add(domain2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_knowledge_point_creation(self, db_session):
        """Test creating a knowledge point"""
        kp = KnowledgePoint(name="Python", description="Python programming")
        db_session.add(kp)
        db_session.commit()
        
        assert kp.id is not None
        assert kp.name == "Python"
        assert kp.description == "Python programming"
        assert kp.created_at is not None
    
    def test_knowledge_point_unique_name(self, db_session):
        """Test that knowledge point names must be unique"""
        kp1 = KnowledgePoint(name="Unique KP")
        db_session.add(kp1)
        db_session.commit()
        
        kp2 = KnowledgePoint(name="Unique KP")
        db_session.add(kp2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_article_domain_relationship(self, db_session, sample_article, sample_domain):
        """Test article-domain many-to-many relationship"""
        assert sample_domain in sample_article.domains
        assert sample_article in sample_domain.articles
    
    def test_article_knowledge_point_relationship(self, db_session, sample_article, sample_knowledge_point):
        """Test article-knowledge point many-to-many relationship"""
        assert sample_knowledge_point in sample_article.knowledge_points
        assert sample_article in sample_knowledge_point.articles
    
    def test_article_multiple_domains(self, db_session):
        """Test article can have multiple domains"""
        domain1 = Domain(name="Domain A")
        domain2 = Domain(name="Domain B")
        db_session.add_all([domain1, domain2])
        
        article = Article(url="https://example.com/multi", title="Multi Domain")
        article.domains.extend([domain1, domain2])
        db_session.add(article)
        db_session.commit()
        
        assert len(article.domains) == 2
        assert domain1 in article.domains
        assert domain2 in article.domains
    
    def test_article_optional_fields(self, db_session):
        """Test article with optional fields set to None"""
        article = Article(
            url="https://example.com/minimal",
            title="Minimal Article"
        )
        db_session.add(article)
        db_session.commit()
        
        assert article.content is None
        assert article.summary is None
        assert article.markdown_path is None
        assert article.neo4j_id is None
        assert article.notion_page_id is None
    
    def test_article_with_integration_ids(self, db_session):
        """Test article with Neo4j and Notion IDs"""
        article = Article(
            url="https://example.com/integrated",
            title="Integrated Article",
            neo4j_id="neo4j-123",
            notion_page_id="notion-456",
            markdown_path="/path/to/file.md"
        )
        db_session.add(article)
        db_session.commit()
        
        assert article.neo4j_id == "neo4j-123"
        assert article.notion_page_id == "notion-456"
        assert article.markdown_path == "/path/to/file.md"
    
    def test_domain_without_description(self, db_session):
        """Test domain can be created without description"""
        domain = Domain(name="No Description")
        db_session.add(domain)
        db_session.commit()
        
        assert domain.description is None
    
    def test_knowledge_point_without_description(self, db_session):
        """Test knowledge point can be created without description"""
        kp = KnowledgePoint(name="No Description")
        db_session.add(kp)
        db_session.commit()
        
        assert kp.description is None


class TestDatabaseFunctions:
    """Tests for database utility functions"""
    
    def test_init_db(self):
        """Test database initialization"""
        # Create a separate test engine
        engine = create_engine("sqlite:///:memory:")
        
        # Bind Base to the engine and create tables
        Base.metadata.create_all(bind=engine)
        
        # Verify tables were created
        from sqlalchemy import inspect
        inspector = inspect(engine)
        table_names = inspector.get_table_names()
        
        assert 'articles' in table_names
        assert 'domains' in table_names
        assert 'knowledge_points' in table_names
        assert 'article_domains' in table_names
        assert 'article_knowledge_points' in table_names
    
    def test_get_db_generator(self):
        """Test that get_db is a generator function"""
        gen = get_db()
        assert hasattr(gen, '__next__')
        # Close the generator to clean up
        try:
            db = next(gen)
            assert db is not None
        except StopIteration:
            pass
        finally:
            gen.close()


class TestAssociationTables:
    """Tests for association tables"""
    
    def test_article_domains_table_exists(self, test_engine):
        """Test article_domains association table"""
        from sqlalchemy import inspect
        inspector = inspect(test_engine)
        
        # Check that the association table exists
        tables = inspector.get_table_names()
        assert 'article_domains' in tables
    
    def test_article_knowledge_points_table_exists(self, test_engine):
        """Test article_knowledge_points association table"""
        from sqlalchemy import inspect
        inspector = inspect(test_engine)
        
        tables = inspector.get_table_names()
        assert 'article_knowledge_points' in tables
    
    def test_remove_article_removes_associations(self, db_session, sample_article, sample_domain, sample_knowledge_point):
        """Test that deleting an article removes its associations"""
        article_id = sample_article.id
        domain_id = sample_domain.id
        kp_id = sample_knowledge_point.id
        
        # Delete the article
        db_session.delete(sample_article)
        db_session.commit()
        
        # Domain and knowledge point should still exist
        domain = db_session.query(Domain).filter(Domain.id == domain_id).first()
        kp = db_session.query(KnowledgePoint).filter(KnowledgePoint.id == kp_id).first()
        
        assert domain is not None
        assert kp is not None
        
        # But article should be gone
        article = db_session.query(Article).filter(Article.id == article_id).first()
        assert article is None
