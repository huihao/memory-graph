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
