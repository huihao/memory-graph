from __future__ import annotations

from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session
try:
    from database import Article
except ImportError:  # pragma: no cover - fallback for package imports
    from backend.database import Article

try:
    from tasks import MarkdownConverter
except ImportError:  # pragma: no cover - fallback for package imports
    from backend.tasks import MarkdownConverter


class ObsidianSync:
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path) if vault_path else None

    def export_article(self, article: Article, db: Session) -> Optional[str]:
        """Export an article to the Obsidian vault drafts folder.

        Args:
            article: Article SQLAlchemy model instance.
            db: Active database session used by the markdown converter.

        Returns:
            Path to the created markdown file, or None if vault path is unset.
        """
        if not self.vault_path:
            return None
        export_dir = self.vault_path / "drafts"
        converter = MarkdownConverter(str(export_dir))
        markdown_path = converter.convert_article_to_markdown(article, db)
        return markdown_path
