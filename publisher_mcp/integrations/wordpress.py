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

    def create_post(
        self,
        title: str,
        slug: str,
        content_html: str,
        status: str = "draft",  # "draft" or "publish"
        excerpt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Post article to WordPress. Operates in dry-run mode if unconfigured or DRY_RUN=true."""
        if not self.is_configured() or self.dry_run:
            # Simulated publication for testing / dry-run
            return {
                "dry_run": True,
                "remote_id": "simulated-wp-999",
                "link": f"https://example.com/wp-preview/{slug}",
                "status": status,
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
