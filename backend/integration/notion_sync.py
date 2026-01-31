from __future__ import annotations

from typing import Dict, Optional
import requests


class NotionSync:
    def __init__(self, api_key: str, database_id: str):
        self.api_key = api_key
        self.database_id = database_id

    def push_bookmark_inbox(self, article: Dict, neo4j_id: Optional[str]) -> Optional[str]:
        """Push a bookmark entry into the Notion inbox database.

        Args:
            article: Dict with required keys: title, url. Optional key: domains (list[str]).
            neo4j_id: Neo4j node ID to store on the Notion page, if available.

        Returns:
            The Notion page ID if created, otherwise None (when not configured).

        Raises:
            RuntimeError: When the Notion API request fails.
        """
        if not self.api_key or not self.database_id:
            return None
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }
        payload = {
            "parent": {"database_id": self.database_id},
            "properties": {
                "Title": {"title": [{"text": {"content": article["title"]}}]},
                "URL": {"url": article["url"]},
                "Status": {"select": {"name": "New"}},
                "Topics": {
                    "multi_select": [
                        {"name": topic} for topic in article.get("domains", [])
                    ]
                },
            },
        }
        if neo4j_id:
            payload["properties"]["Neo4j ID"] = {
                "rich_text": [{"text": {"content": neo4j_id}}]
            }
        try:
            response = requests.post(
                "https://api.notion.com/v1/pages",
                json=payload,
                headers=headers,
                timeout=10,
            )
            response.raise_for_status()
            return response.json().get("id")
        except requests.RequestException as exc:
            raise RuntimeError(f"Notion sync failed: {exc}") from exc
