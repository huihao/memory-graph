from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Table, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime

Base = declarative_base()

# Association table for many-to-many relationship between articles and knowledge points
article_knowledge_points = Table(
    'article_knowledge_points',
    Base.metadata,
    Column('article_id', Integer, ForeignKey('articles.id')),
    Column('knowledge_point_id', Integer, ForeignKey('knowledge_points.id'))
)

# Association table for many-to-many relationship between articles and domains
article_domains = Table(
    'article_domains',
    Base.metadata,
    Column('article_id', Integer, ForeignKey('articles.id')),
    Column('domain_id', Integer, ForeignKey('domains.id'))
)

class Article(Base):
    __tablename__ = 'articles'
    
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text)
    summary = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    markdown_path = Column(String)  # Path to generated Obsidian markdown file
    
    # Relationships
    domains = relationship('Domain', secondary=article_domains, back_populates='articles')
    knowledge_points = relationship('KnowledgePoint', secondary=article_knowledge_points, back_populates='articles')

class Domain(Base):
    __tablename__ = 'domains'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    articles = relationship('Article', secondary=article_domains, back_populates='domains')

class KnowledgePoint(Base):
    __tablename__ = 'knowledge_points'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    articles = relationship('Article', secondary=article_knowledge_points, back_populates='knowledge_points')

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./memory_graph.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
