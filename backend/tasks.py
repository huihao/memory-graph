import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Iterable, Tuple, Set
from sqlalchemy.orm import Session
try:
    from database import Article, Domain, KnowledgePoint
except ImportError:  # pragma: no cover - fallback for package imports
    from backend.database import Article, Domain, KnowledgePoint

MAX_TITLE_LENGTH = 100
MAX_RELATED_ARTICLES = 10

class MarkdownConverter:
    """Service for converting articles to Obsidian markdown format"""
    
    def __init__(self, export_dir: str = "./exports"):
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)
    
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
        safe_title = self._safe_title(article)
        filename = f"{safe_title}.md"
        filepath = self.export_dir / filename
        
        # Build markdown content
        markdown_content = self._build_markdown_content(article)
        
        # Write to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        return str(filepath)
    
    def _safe_title(self, article: Article) -> str:
        safe_title = "".join(c for c in article.title if c.isalnum() or c in (" ", "-", "_")).rstrip()
        safe_title = safe_title[:MAX_TITLE_LENGTH].rstrip()
        return safe_title if safe_title else f"article-{article.id}"

    def _format_wiki_link(self, article: Article) -> str:
        safe_title = self._safe_title(article)
        if safe_title == article.title:
            return f"[[{safe_title}]]"
        return f"[[{safe_title}|{article.title}]]"

    def _dedupe_articles(self, articles: Iterable[Article]) -> List[Article]:
        deduped = {article.id: article for article in articles}
        return list(deduped.values())

    def _collect_related_articles(self, article: Article) -> Dict[str, List[Article]]:
        related_by_domain = self._dedupe_articles(
            related
            for domain in article.domains
            for related in domain.articles
            if related.id != article.id
        )
        related_by_kp = self._dedupe_articles(
            related
            for kp in article.knowledge_points
            for related in kp.articles
            if related.id != article.id
        )
        related_domain_article_ids = {a.id for a in related_by_domain}
        related_by_kp = [related for related in related_by_kp if related.id not in related_domain_article_ids]
        return {
            "by_domain": related_by_domain,
            "by_knowledge_point": related_by_kp,
        }

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
        if article.neo4j_id:
            lines.append(f"neo4j_id: {article.neo4j_id}")
        if article.notion_page_id:
            lines.append(f"notion_page_id: {article.notion_page_id}")
        
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

        related = self._collect_related_articles(article)
        if related["by_domain"] or related["by_knowledge_point"]:
            lines.append("## Related Articles")
            if related["by_domain"]:
                lines.append("### Same Domain")
                for related_article in related["by_domain"][:MAX_RELATED_ARTICLES]:
                    lines.append(f"- {self._format_wiki_link(related_article)}")
                lines.append("")
            if related["by_knowledge_point"]:
                lines.append("### Same Knowledge Points")
                for related_article in related["by_knowledge_point"][:MAX_RELATED_ARTICLES]:
                    lines.append(f"- {self._format_wiki_link(related_article)}")
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

        related_domain_article_ids = {related.id for related in related_by_domain}
        related_by_kp = {related for related in related_by_kp if related.id not in related_domain_article_ids}
        
        return {
            "by_domain": list(related_by_domain),
            "by_knowledge_point": list(related_by_kp)
        }
    
    def get_knowledge_graph_data(
        self,
        db: Session,
        domain_id: Optional[int] = None,
        knowledge_point_id: Optional[int] = None,
    ) -> Dict:
        """
        Get data for visualizing the knowledge graph
        
        Returns:
            Dictionary with nodes and edges for graph visualization
        """
        context = {"domain": None, "knowledge_point": None}
        if domain_id:
            domain = db.query(Domain).filter(Domain.id == domain_id).first()
            if not domain:
                return {"nodes": [], "edges": [], "context": context}
            articles = list(domain.articles)
            domains = [domain]
            knowledge_points = list({kp for article in articles for kp in article.knowledge_points})
            context["domain"] = domain.name
        elif knowledge_point_id:
            kp = db.query(KnowledgePoint).filter(KnowledgePoint.id == knowledge_point_id).first()
            if not kp:
                return {"nodes": [], "edges": [], "context": context}
            articles = list(kp.articles)
            knowledge_points = [kp]
            domains = list({domain for article in articles for domain in article.domains})
            context["knowledge_point"] = kp.name
        else:
            articles = db.query(Article).all()
            domains = db.query(Domain).all()
            knowledge_points = db.query(KnowledgePoint).all()
        
        nodes = []
        edges = []
        edge_keys: Set[Tuple[str, str, str]] = set()
        article_edge_map: Dict[Tuple[int, int], Dict[str, set]] = {}

        def add_edge(source: str, target: str, edge_type: str) -> None:
            if source == target:
                return
            key = (source, target, edge_type)
            if key in edge_keys or (target, source, edge_type) in edge_keys:
                return
            edges.append({
                "source": source,
                "target": target,
                "type": edge_type
            })
            edge_keys.add(key)

        def add_article_relation(article_a: Article, article_b: Article, relation_type: str, label: str) -> None:
            pair_key = tuple(sorted((article_a.id, article_b.id)))
            entry = article_edge_map.setdefault(pair_key, {"domains": set(), "knowledge_points": set()})
            entry[relation_type].add(label)
        
        # Add article nodes
        for article in articles:
            nodes.append({
                "id": f"article_{article.id}",
                "label": article.title[:50],
                "type": "article",
                "url": article.url,
                "icon": "📄",
                "size": max(6, (len(article.domains) + len(article.knowledge_points)) * 2)
            })
        
        # Add domain nodes
        for domain in domains:
            nodes.append({
                "id": f"domain_{domain.id}",
                "label": domain.name,
                "type": "domain",
                "icon": "🧭",
                "size": max(8, len(domain.articles) * 2)
            })
            
            # Add edges between articles and domains
            for article in domain.articles:
                add_edge(f"article_{article.id}", f"domain_{domain.id}", "belongs_to")
            domain_articles = list(domain.articles)
            for first_index in range(len(domain_articles)):
                for second_index in range(first_index + 1, len(domain_articles)):
                    add_article_relation(
                        domain_articles[first_index],
                        domain_articles[second_index],
                        "domains",
                        domain.name
                    )
        
        # Add knowledge point nodes
        for kp in knowledge_points:
            nodes.append({
                "id": f"kp_{kp.id}",
                "label": kp.name,
                "type": "knowledge_point",
                "icon": "💡",
                "size": max(8, len(kp.articles) * 2)
            })
            
            # Add edges between articles and knowledge points
            for article in kp.articles:
                add_edge(f"article_{article.id}", f"kp_{kp.id}", "covers")
            kp_articles = list(kp.articles)
            for first_index in range(len(kp_articles)):
                for second_index in range(first_index + 1, len(kp_articles)):
                    add_article_relation(
                        kp_articles[first_index],
                        kp_articles[second_index],
                        "knowledge_points",
                        kp.name
                    )

        for (source_id, target_id), relation_data in article_edge_map.items():
            edges.append({
                "source": f"article_{source_id}",
                "target": f"article_{target_id}",
                "type": "related_articles",
                "shared_domains": sorted(relation_data["domains"]),
                "shared_knowledge_points": sorted(relation_data["knowledge_points"]),
                "weight": len(relation_data["domains"]) + len(relation_data["knowledge_points"])
            })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "context": context
        }
