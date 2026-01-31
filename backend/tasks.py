import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict
from sqlalchemy.orm import Session
from database import Article, Domain, KnowledgePoint

class MarkdownConverter:
    """Service for converting articles to Obsidian markdown format"""
    
    def __init__(self, export_dir: str = "./exports"):
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(exist_ok=True)
    
    def convert_article_to_markdown(self, article: Article, db: Session) -> str:
        """
        Convert an article to Obsidian markdown format
        
        Args:
            article: Article object from database
            db: Database session
            
        Returns:
            Path to the created markdown file
        """
        # Create filename from title (sanitize for filesystem)
        safe_title = "".join(c for c in article.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_title = safe_title[:100]  # Limit length
        filename = f"{safe_title}.md"
        filepath = self.export_dir / filename
        
        # Build markdown content
        markdown_content = self._build_markdown_content(article)
        
        # Write to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        return str(filepath)
    
    def _build_markdown_content(self, article: Article) -> str:
        """Build the markdown content with Obsidian formatting"""
        lines = []
        
        # Title
        lines.append(f"# {article.title}\n")
        
        # Metadata
        lines.append("---")
        lines.append(f"url: {article.url}")
        lines.append(f"created: {article.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"updated: {article.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Tags for domains
        if article.domains:
            tags = [f"#{domain.name.replace(' ', '-')}" for domain in article.domains]
            lines.append(f"tags: {' '.join(tags)}")
        
        lines.append("---\n")
        
        # Domains section
        if article.domains:
            lines.append("## Domains")
            for domain in article.domains:
                lines.append(f"- [[{domain.name}]]")
            lines.append("")
        
        # Knowledge Points section
        if article.knowledge_points:
            lines.append("## Knowledge Points")
            for kp in article.knowledge_points:
                lines.append(f"- [[{kp.name}]]")
            lines.append("")
        
        # Summary
        if article.summary:
            lines.append("## Summary")
            lines.append(article.summary)
            lines.append("")
        
        # Content
        lines.append("## Content")
        if article.content:
            lines.append(article.content[:5000])  # Limit content length
        
        # Links section
        lines.append("\n## Source")
        lines.append(f"[Original Article]({article.url})")
        
        return "\n".join(lines)
    
    def batch_convert(self, db: Session, limit: int = None) -> List[str]:
        """
        Convert all articles to markdown
        
        Args:
            db: Database session
            limit: Optional limit on number of articles to convert
            
        Returns:
            List of created file paths
        """
        query = db.query(Article)
        if limit:
            query = query.limit(limit)
        
        articles = query.all()
        filepaths = []
        
        for article in articles:
            try:
                filepath = self.convert_article_to_markdown(article, db)
                filepaths.append(filepath)
                
                # Update article with markdown path
                article.markdown_path = filepath
                db.commit()
            except Exception as e:
                print(f"Error converting article {article.id}: {e}")
                db.rollback()
        
        return filepaths

class KnowledgeGraphService:
    """Service for creating connections between articles based on domains and knowledge points"""
    
    def find_related_articles(self, article_id: int, db: Session) -> Dict[str, List[Article]]:
        """
        Find articles related to the given article
        
        Args:
            article_id: ID of the article
            db: Database session
            
        Returns:
            Dictionary with 'by_domain' and 'by_knowledge_point' lists
        """
        article = db.query(Article).filter(Article.id == article_id).first()
        if not article:
            return {"by_domain": [], "by_knowledge_point": []}
        
        # Find articles in same domains
        related_by_domain = set()
        for domain in article.domains:
            for related_article in domain.articles:
                if related_article.id != article_id:
                    related_by_domain.add(related_article)
        
        # Find articles with same knowledge points
        related_by_kp = set()
        for kp in article.knowledge_points:
            for related_article in kp.articles:
                if related_article.id != article_id:
                    related_by_kp.add(related_article)
        
        return {
            "by_domain": list(related_by_domain),
            "by_knowledge_point": list(related_by_kp)
        }
    
    def get_knowledge_graph_data(self, db: Session) -> Dict:
        """
        Get data for visualizing the knowledge graph
        
        Returns:
            Dictionary with nodes and edges for graph visualization
        """
        articles = db.query(Article).all()
        domains = db.query(Domain).all()
        knowledge_points = db.query(KnowledgePoint).all()
        
        nodes = []
        edges = []
        
        # Add article nodes
        for article in articles:
            nodes.append({
                "id": f"article_{article.id}",
                "label": article.title[:50],
                "type": "article",
                "url": article.url
            })
        
        # Add domain nodes
        for domain in domains:
            nodes.append({
                "id": f"domain_{domain.id}",
                "label": domain.name,
                "type": "domain"
            })
            
            # Add edges between articles and domains
            for article in domain.articles:
                edges.append({
                    "source": f"article_{article.id}",
                    "target": f"domain_{domain.id}",
                    "type": "belongs_to"
                })
        
        # Add knowledge point nodes
        for kp in knowledge_points:
            nodes.append({
                "id": f"kp_{kp.id}",
                "label": kp.name,
                "type": "knowledge_point"
            })
            
            # Add edges between articles and knowledge points
            for article in kp.articles:
                edges.append({
                    "source": f"article_{article.id}",
                    "target": f"kp_{kp.id}",
                    "type": "covers"
                })
        
        return {
            "nodes": nodes,
            "edges": edges
        }
