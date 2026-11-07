"""WordPress REST API integration adapter."""

import os
import httpx
from typing import Any, Dict, Optional


class WordPressClient:
    def __init__(
        self,
        api_url: Optional[str] = None,
        username: Optional[str] = None,
        app_password: Optional[str] = None,
    ):
        self.api_url = (api_url or os.getenv("WP_API_URL", "")).rstrip("/")
        self.username = username or os.getenv("WP_USERNAME", "")
        self.app_password = app_password or os.getenv("WP_APP_PASSWORD", "")
        self.dry_run = os.getenv("DRY_RUN", "true").lower() in ("true", "1", "yes")

    def is_configured(self) -> bool:
        return bool(self.api_url and self.username and self.app_password)

    def upload_media(
        self,
        image_bytes: bytes,
        filename: str,
        mime_type: str = "image/png",
        alt_text: str = "",
    ) -> Dict[str, Any]:
        """Upload media to WordPress via REST API (/wp/v2/media) or simulate in dry-run mode."""
        if not self.is_configured() or self.dry_run:
            return {
                "dry_run": True,
                "media_id": 888,
                "source_url": f"https://example.com/wp-content/uploads/{filename}",
                "alt_text": alt_text,
                "message": "Simulated WordPress media upload.",
            }

        endpoint = f"{self.api_url}/media"
        headers = {
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": mime_type,
        }
        auth = (self.username, self.app_password)
        with httpx.Client(timeout=45.0) as client:
            resp = client.post(endpoint, content=image_bytes, headers=headers, auth=auth)
            resp.raise_for_status()
            data = resp.json()
            return {
                "dry_run": False,
                "media_id": data.get("id"),
                "source_url": data.get("source_url"),
                "alt_text": alt_text,
                "raw_response": data,
            }

    def create_post(
        self,
        title: str,
        slug: str,
        content_html: str,
        status: str = "draft",  # "draft" or "publish"
        excerpt: Optional[str] = None,
        categories: Optional[list] = None,
        tags: Optional[list] = None,
        featured_media_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Post article to WordPress. Operates in dry-run mode if unconfigured or DRY_RUN=true."""
        if not self.is_configured() or self.dry_run:
            # Simulated publication for testing / dry-run
            return {
                "dry_run": True,
                "remote_id": "simulated-wp-999",
                "link": f"https://example.com/wp-preview/{slug}",
                "status": status,
                "categories": categories or [],
                "tags": tags or [],
                "featured_media": featured_media_id or 888,
                "message": "Simulated WordPress post creation (DRY_RUN mode active or credentials unconfigured).",
            }

        endpoint = f"{self.api_url}/posts"
        payload = {
            "title": title,
            "slug": slug,
            "content": content_html,
            "status": status,
        }
        if excerpt:
            payload["excerpt"] = excerpt
        if categories:
            payload["categories"] = categories
        if tags:
            payload["tags"] = tags
        if featured_media_id:
            payload["featured_media"] = featured_media_id

        auth = (self.username, self.app_password)
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(endpoint, json=payload, auth=auth)
            resp.raise_for_status()
            data = resp.json()
            return {
                "dry_run": False,
                "remote_id": str(data.get("id")),
                "link": data.get("link"),
                "status": data.get("status"),
                "raw_response": data,
            }

    def verify_post(self, remote_post_id: str) -> Dict[str, Any]:
        """Verify an existing post on WordPress."""
        if not self.is_configured() or self.dry_run:
            return {
                "dry_run": True,
                "verified": True,
                "remote_id": remote_post_id,
                "message": "Simulated verification successful.",
            }

        endpoint = f"{self.api_url}/posts/{remote_post_id}"
        auth = (self.username, self.app_password)
        with httpx.Client(timeout=30.0) as client:
            resp = client.get(endpoint, auth=auth)
            resp.raise_for_status()
            data = resp.json()
            return {
                "dry_run": False,
                "verified": True,
                "remote_id": str(data.get("id")),
                "status": data.get("status"),
                "link": data.get("link"),
            }
