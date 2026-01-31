from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uvicorn

from database import init_db, get_db, Article as DBArticle, Domain as DBDomain, KnowledgePoint as DBKnowledgePoint
from schemas import Article, ArticleCreate, ArticleList, Domain, KnowledgePoint
from services import LLMService, ContentExtractor
from tasks import MarkdownConverter, KnowledgeGraphService
import logging
from integration.neo4j_sync import Neo4jSync
from integration.notion_sync import NotionSync
from integration.obsidian_sync import ObsidianSync

app = FastAPI(title="Memory Graph API", version="1.0.0")
logger = logging.getLogger(__name__)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
llm_service = LLMService()
content_extractor = ContentExtractor()
markdown_converter = MarkdownConverter()
knowledge_graph_service = KnowledgeGraphService()
neo4j_sync = None
notion_sync = None
obsidian_sync = None

@app.on_event("startup")
async def startup_event():
    init_db()
    global neo4j_sync, notion_sync, obsidian_sync
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "")
    notion_api_key = os.getenv("NOTION_API_KEY", "")
    notion_inbox_db_id = os.getenv("NOTION_INBOX_DB_ID", "")
    obsidian_vault_path = os.getenv("OBSIDIAN_VAULT_PATH", "")
    try:
        neo4j_sync = Neo4jSync(
            neo4j_uri,
            neo4j_user,
            neo4j_password,
        )
    except ValueError as exc:
        logger.warning("Neo4j integration disabled: %s", exc)
        neo4j_sync = None

    notion_sync = None
    if notion_api_key and notion_inbox_db_id:
        notion_sync = NotionSync(
            notion_api_key,
            notion_inbox_db_id,
        )
    else:
        logger.info("Notion integration disabled: missing configuration.")

    obsidian_sync = None
    if obsidian_vault_path:
        obsidian_sync = ObsidianSync(obsidian_vault_path)
    else:
        logger.info("Obsidian integration disabled: missing vault path.")

@app.on_event("shutdown")
async def shutdown_event():
    if neo4j_sync:
        neo4j_sync.close()

@app.get("/")
async def root():
    return {"message": "Memory Graph API", "version": "1.0.0"}

@app.post("/api/articles", response_model=Article)
async def create_article(article: ArticleCreate, db: Session = Depends(get_db)):
    """Create a new article with domains and knowledge points"""
    
    # Check if article already exists
    existing = db.query(DBArticle).filter(DBArticle.url == article.url).first()
    if existing:
        raise HTTPException(status_code=400, detail="Article with this URL already exists")
    
    # Create article
    db_article = DBArticle(
        url=article.url,
        title=article.title,
        content=article.content,
        summary=article.summary
    )
    
    # Process domains
    for domain_name in article.domain_names:
        domain = db.query(DBDomain).filter(DBDomain.name == domain_name).first()
        if not domain:
            domain = DBDomain(name=domain_name)
            db.add(domain)
        db_article.domains.append(domain)
    
    # Process knowledge points
    for kp_name in article.knowledge_point_names:
        kp = db.query(DBKnowledgePoint).filter(DBKnowledgePoint.name == kp_name).first()
        if not kp:
            kp = DBKnowledgePoint(name=kp_name)
            db.add(kp)
        db_article.knowledge_points.append(kp)
    
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    
    return db_article

@app.get("/api/articles", response_model=ArticleList)
async def get_articles(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all articles with pagination"""
    articles = db.query(DBArticle).offset(skip).limit(limit).all()
    total = db.query(DBArticle).count()
    return {"articles": articles, "total": total}

@app.get("/api/articles/{article_id}", response_model=Article)
async def get_article(article_id: int, db: Session = Depends(get_db)):
    """Get a specific article by ID"""
    article = db.query(DBArticle).filter(DBArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article

@app.post("/api/articles/analyze-url")
async def analyze_url(url: str, db: Session = Depends(get_db)):
    """
    Extract content from URL and analyze it with LLM
    This endpoint is called by the browser extension
    """
    # Extract content
    extracted = await content_extractor.extract_content(url)
    
    # Analyze with LLM
    existing_domains = [domain.name for domain in db.query(DBDomain).all()]
    existing_kps = [kp.name for kp in db.query(DBKnowledgePoint).all()]
    analysis = await llm_service.analyze_article(
        extracted["title"],
        extracted["content"],
        existing_domains=existing_domains,
        existing_knowledge_points=existing_kps
    )
    
    # Create article
    article = ArticleCreate(
        url=url,
        title=extracted["title"],
        content=extracted["content"][:10000],  # Limit content length
        summary="",
        domain_names=analysis.get("domains", []),
        knowledge_point_names=analysis.get("knowledge_points", [])
    )
    
    # Check if already exists
    existing = db.query(DBArticle).filter(DBArticle.url == url).first()
    if existing:
        return {"status": "exists", "article_id": existing.id, "article": existing}
    
    # Save to database
    db_article = DBArticle(
        url=article.url,
        title=article.title,
        content=article.content,
        summary=article.summary
    )
    
    # Process domains
    for domain_name in article.domain_names:
        domain = db.query(DBDomain).filter(DBDomain.name == domain_name).first()
        if not domain:
            domain = DBDomain(name=domain_name)
            db.add(domain)
        db_article.domains.append(domain)
    
    # Process knowledge points
    for kp_name in article.knowledge_point_names:
        kp = db.query(DBKnowledgePoint).filter(DBKnowledgePoint.name == kp_name).first()
        if not kp:
            kp = DBKnowledgePoint(name=kp_name)
            db.add(kp)
        db_article.knowledge_points.append(kp)
    
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    
    return {"status": "created", "article_id": db_article.id, "article": db_article}

@app.get("/api/domains", response_model=List[Domain])
async def get_domains(db: Session = Depends(get_db)):
    """Get all domains"""
    return db.query(DBDomain).all()

@app.get("/api/knowledge-points", response_model=List[KnowledgePoint])
async def get_knowledge_points(db: Session = Depends(get_db)):
    """Get all knowledge points"""
    return db.query(DBKnowledgePoint).all()

@app.post("/api/tasks/convert-to-markdown")
async def convert_to_markdown(limit: int = None, db: Session = Depends(get_db)):
    """Convert all articles to Obsidian markdown format"""
    filepaths = markdown_converter.batch_convert(db, limit)
    return {"status": "success", "converted": len(filepaths), "files": filepaths}

@app.get("/api/articles/{article_id}/related")
async def get_related_articles(article_id: int, db: Session = Depends(get_db)):
    """Get articles related to a specific article"""
    related = knowledge_graph_service.find_related_articles(article_id, db)
    return {
        "by_domain": related["by_domain"],
        "by_knowledge_point": related["by_knowledge_point"]
    }

@app.get("/api/knowledge-graph")
async def get_knowledge_graph(
    domain_id: Optional[int] = None,
    knowledge_point_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get knowledge graph data for visualization"""
    if domain_id and knowledge_point_id:
        raise HTTPException(status_code=400, detail="Provide only one filter at a time")
    return knowledge_graph_service.get_knowledge_graph_data(
        db,
        domain_id=domain_id,
        knowledge_point_id=knowledge_point_id
    )

@app.post("/api/sync/full-pipeline")
async def full_sync_pipeline(article_id: int, db: Session = Depends(get_db)):
    """Sync an article to Neo4j, Notion, and Obsidian Drafts.

    Args:
        article_id: Article ID to sync.

    Returns:
        Sync status and updated integration identifiers.

    Raises:
        HTTPException: 404 if the article does not exist.
    """
    article = db.query(DBArticle).filter(DBArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    article_payload = {
        "url": article.url,
        "title": article.title,
        "markdown_path": article.markdown_path,
        "notion_page_id": article.notion_page_id,
    }
    neo4j_id = article.neo4j_id
    if neo4j_sync:
        neo4j_id = neo4j_sync.sync_article(article_payload, article.neo4j_id)

    notion_page_id = None
    if notion_sync:
        try:
            notion_page_id = notion_sync.push_bookmark_inbox(
                {
                    "url": article.url,
                    "title": article.title,
                    "domains": [domain.name for domain in article.domains],
                },
                neo4j_id,
            )
        except RuntimeError as exc:
            logger.error("Notion sync failed: %s", exc)

    markdown_path = None
    if obsidian_sync:
        try:
            markdown_path = obsidian_sync.export_article(article, db)
        except Exception as exc:
            logger.error("Obsidian export failed: %s", exc)

    if neo4j_id:
        article.neo4j_id = neo4j_id
    if notion_page_id:
        article.notion_page_id = notion_page_id
    if markdown_path:
        article.markdown_path = markdown_path
    db.commit()
    db.refresh(article)

    return {
        "status": "synced",
        "article_id": article.id,
        "neo4j_id": article.neo4j_id,
        "notion_page_id": article.notion_page_id,
        "markdown_path": article.markdown_path,
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
