from __future__ import annotations

from typing import Dict, Optional
from uuid import uuid4
from neo4j import GraphDatabase


class Neo4jSync:
    def __init__(self, uri: str, user: str, password: str):
        if not password:
            raise ValueError("NEO4J_PASSWORD must be set for Neo4j integration.")
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self) -> None:
        self.driver.close()

    def sync_article(self, article: Dict, neo4j_id: Optional[str] = None) -> str:
        """Sync an article to Neo4j as a Bookmark node.

        Args:
            article: Dict with required keys: url, title. Optional keys:
                markdown_path, notion_page_id.
            neo4j_id: Existing Neo4j node ID to update. If None, a new ID is generated.

        Returns:
            The Neo4j node ID for the bookmark.
        """
        with self.driver.session() as session:
            result = session.run(
                """
                MERGE (b:Bookmark {id: $neo_id})
                SET b.url = $url,
                    b.title = $title,
                    b.obsidian_path = $obsidian_path,
                    b.notion_page_id = $notion_page_id,
                    b.synced_at = datetime()
                RETURN b.id AS neo4j_id
                """,
                neo_id=neo4j_id or f"bookmark-{uuid4().hex}",
                url=article["url"],
                title=article["title"],
                obsidian_path=article.get("markdown_path"),
                notion_page_id=article.get("notion_page_id"),
            )
            return result.single()["neo4j_id"]
