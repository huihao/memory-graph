"""
Pytest fixtures and shared test configuration
"""
import os
import sys
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Base, Article, Domain, KnowledgePoint


@pytest.fixture(scope="function")
def test_engine():
    """Create a new in-memory SQLite database for each test"""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(test_engine):
    """Create a database session for testing"""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def sample_domain(db_session):
    """Create a sample domain"""
    domain = Domain(name="Machine Learning", description="ML domain")
    db_session.add(domain)
    db_session.commit()
    db_session.refresh(domain)
    return domain


@pytest.fixture
def sample_knowledge_point(db_session):
    """Create a sample knowledge point"""
    kp = KnowledgePoint(name="Neural Networks", description="Deep learning concepts")
    db_session.add(kp)
    db_session.commit()
    db_session.refresh(kp)
    return kp


@pytest.fixture
def sample_article(db_session, sample_domain, sample_knowledge_point):
    """Create a sample article with relationships"""
    article = Article(
        url="https://example.com/article",
        title="Test Article",
        content="This is test content about machine learning and neural networks.",
        summary="Test summary",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    article.domains.append(sample_domain)
    article.knowledge_points.append(sample_knowledge_point)
    db_session.add(article)
    db_session.commit()
    db_session.refresh(article)
    return article


@pytest.fixture
def multiple_articles(db_session):
    """Create multiple articles with domains and knowledge points"""
    # Create domains
    domain1 = Domain(name="Web Development")
    domain2 = Domain(name="Cloud Computing")
    db_session.add_all([domain1, domain2])
    
    # Create knowledge points
    kp1 = KnowledgePoint(name="React")
    kp2 = KnowledgePoint(name="Docker")
    kp3 = KnowledgePoint(name="Kubernetes")
    db_session.add_all([kp1, kp2, kp3])
    
    db_session.commit()
    
    # Create articles
    article1 = Article(
        url="https://example.com/article1",
        title="React Fundamentals",
        content="Learn React basics",
        summary="React intro"
    )
    article1.domains.append(domain1)
    article1.knowledge_points.append(kp1)
    
    article2 = Article(
        url="https://example.com/article2",
        title="Docker and Kubernetes",
        content="Container orchestration with Docker and K8s",
        summary="Containers guide"
    )
    article2.domains.append(domain2)
    article2.knowledge_points.extend([kp2, kp3])
    
    article3 = Article(
        url="https://example.com/article3",
        title="Full Stack Development",
        content="Web development with cloud deployment",
        summary="Full stack guide"
    )
    article3.domains.extend([domain1, domain2])
    article3.knowledge_points.extend([kp1, kp2])
    
    db_session.add_all([article1, article2, article3])
    db_session.commit()
    
    return {
        "articles": [article1, article2, article3],
        "domains": [domain1, domain2],
        "knowledge_points": [kp1, kp2, kp3]
    }
