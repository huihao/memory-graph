from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from datetime import datetime

class DomainBase(BaseModel):
    name: str
    description: Optional[str] = None

class DomainCreate(DomainBase):
    pass

class Domain(DomainBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class KnowledgePointBase(BaseModel):
    name: str
    description: Optional[str] = None

class KnowledgePointCreate(KnowledgePointBase):
    pass

class KnowledgePoint(KnowledgePointBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class ArticleBase(BaseModel):
    url: str
    title: str
    content: Optional[str] = None
    summary: Optional[str] = None

class ArticleCreate(ArticleBase):
    domain_names: List[str] = []
    knowledge_point_names: List[str] = []

class Article(ArticleBase):
    id: int
    created_at: datetime
    updated_at: datetime
    markdown_path: Optional[str] = None
    neo4j_id: Optional[str] = None
    notion_page_id: Optional[str] = None
    domains: List[Domain] = []
    knowledge_points: List[KnowledgePoint] = []
    
    class Config:
        from_attributes = True

class ArticleList(BaseModel):
    articles: List[Article]
    total: int

class SearchResult(BaseModel):
    """Response model for search results with pagination info"""
    articles: List[Article]
    total: int
    skip: int
    limit: int
    has_more: bool

class DomainStats(BaseModel):
    """Domain statistics for the stats endpoint"""
    id: int
    name: str
    article_count: int

class Stats(BaseModel):
    """Aggregate statistics response model"""
    total_articles: int
    total_domains: int
    total_knowledge_points: int
    recent_articles: int
    top_domains: List[DomainStats]
