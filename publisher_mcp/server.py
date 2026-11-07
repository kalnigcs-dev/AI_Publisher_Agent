"""Publisher MCP Server providing state persistence, validation, and publishing gate."""

import os
import sys
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()
from mcp.server.mcpserver import MCPServer
from publisher_mcp.database import db
from publisher_mcp.validation.engine import validate_article_content
from publisher_mcp.integrations.wordpress import WordPressClient
from publisher_mcp.integrations.media import generate_featured_banner

# Initialize database schema if not already initialized
db.init_db()

# Initialize MCP server
mcp = MCPServer(
    name="ai-publisher",
    instructions="MCP server providing persistent state, validation, and gated publishing for AI Publisher.",
)


@mcp.tool()
def ping() -> str:
    """Check health and connectivity of the AI Publisher MCP server."""
    return "pong"


@mcp.tool()
def get_system_status() -> dict:
    """Return runtime environment status and database connectivity info."""
    db_file = db.get_db_path()
    return {
        "status": "online",
        "service": "ai-publisher-mcp",
        "version": "0.1.0",
        "python_version": sys.version,
        "database_path": str(db_file),
        "database_exists": db_file.exists(),
    }


# --- Site Tools ---

@mcp.tool()
def list_sites() -> List[Dict[str, Any]]:
    """List all configured publisher sites, their niches, and target audiences."""
    return db.list_sites()


@mcp.tool()
def get_site_profile(site_id_or_slug: str) -> Optional[Dict[str, Any]]:
    """Get the full profile, niche, language, and editorial guidelines for a specific site."""
    return db.get_site_profile(site_id_or_slug)


@mcp.tool()
def register_site(
    slug: str,
    name: str,
    url: str,
    niche: str,
    language: str = "en",
    editorial_rules: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Register a new site/blog target in the publisher system."""
    site_id = db.create_site(
        slug=slug,
        name=name,
        url=url,
        niche=niche,
        language=language,
        editorial_rules=editorial_rules or {},
    )
    return {"site_id": site_id, "slug": slug, "status": "created"}


# --- Topic Tools ---

@mcp.tool()
def find_duplicate_topics(
    site_id: int,
    slug: str,
    target_keyword: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Check if a topic with the same slug or target keyword already exists for the site."""
    return db.find_duplicate_topics(site_id=site_id, query_slug=slug, query_keyword=target_keyword)


@mcp.tool()
def register_topic(
    site_id: int,
    title: str,
    slug: str,
    target_keyword: str,
    section: str = "general",
    rationale: Optional[str] = None,
) -> Dict[str, Any]:
    """Register a newly proposed article topic into the pipeline with a category/section."""
    dupes = db.find_duplicate_topics(site_id=site_id, query_slug=slug, query_keyword=target_keyword)
    if dupes:
        return {
            "status": "rejected",
            "reason": f"Duplicate topic detected with matching slug or keyword: {dupes[0]['title']} (id: {dupes[0]['id']})",
            "duplicates": dupes,
        }

    topic_id = db.register_topic(
        site_id=site_id,
        title=title,
        slug=slug,
        target_keyword=target_keyword,
        section=section,
        rationale=rationale,
    )
    return {"status": "registered", "topic_id": topic_id, "slug": slug, "section": section}


# --- Research Tools ---

@mcp.tool()
def save_research(
    topic_id: int,
    url: str,
    title: Optional[str] = None,
    snippet: Optional[str] = None,
    is_verified: bool = True,
) -> Dict[str, Any]:
    """Record a verified research source and evidence snippet for a topic."""
    source_id = db.save_research_source(
        topic_id=topic_id,
        url=url,
        title=title,
        snippet=snippet,
        is_verified=is_verified,
    )
    return {"status": "saved", "source_id": source_id, "topic_id": topic_id}


@mcp.tool()
def get_research(topic_id: int) -> List[Dict[str, Any]]:
    """Retrieve all collected research sources and evidence notes for a topic."""
    return db.get_research_sources(topic_id=topic_id)


# --- Article Tools ---

@mcp.tool()
def save_article(
    topic_id: int,
    site_id: int,
    title: str,
    slug: str,
    content_html: str,
    section: Optional[str] = None,
    meta_description: Optional[str] = None,
    change_summary: Optional[str] = None,
) -> Dict[str, Any]:
    """Store or update an article draft in SQLite with automatic version tracking."""
    result = db.save_article(
        topic_id=topic_id,
        site_id=site_id,
        title=title,
        slug=slug,
        content_html=content_html,
        section=section,
        meta_description=meta_description,
        change_summary=change_summary,
    )
    return {"status": "saved", **result}


@mcp.tool()
def get_article(article_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve the current version of an article and its state."""
    return db.get_article(article_id=article_id)


# --- Validation Tools ---

@mcp.tool()
def validate_article(article_id: int) -> Dict[str, Any]:
    """Run deterministic validation checks on an article draft. Transitions state to APPROVED or VALIDATION_FAILED."""
    article = db.get_article(article_id=article_id)
    if not article:
        return {"status": "error", "message": f"Article {article_id} not found."}

    # Fetch site profile
    site = db.get_site_profile(article["site_id"])
    editorial_rules = (site or {}).get("editorial_rules") or {}
    min_words = editorial_rules.get("min_word_count", 150)
    extra_forbidden = editorial_rules.get("forbidden_keywords", [])

    # Fetch research sources
    sources = db.get_research_sources(article["topic_id"])

    # Run validation
    report = validate_article_content(
        title=article["title"],
        slug=article["slug"],
        content_html=article.get("content_html") or "",
        meta_description=article.get("meta_description"),
        sources=sources,
        min_word_count=min_words,
        extra_forbidden_keywords=extra_forbidden,
    )

    # Record in database
    db.record_validation_result(
        article_id=article_id,
        version_id=article["current_version_id"],
        passed=report.passed,
        checks_run=report.checks_run,
        errors=report.errors,
        warnings=report.warnings,
    )

    return {
        "article_id": article_id,
        "passed": report.passed,
        "new_status": "APPROVED" if report.passed else "VALIDATION_FAILED",
        "checks_run": report.checks_run,
        "errors": report.errors,
        "warnings": report.warnings,
        "metrics": report.metrics,
    }


# --- Publishing Tools (Quality Gated) ---

@mcp.tool()
def publish_article(article_id: int, as_draft: bool = True) -> Dict[str, Any]:
    """Quality-gated publishing tool. Strictly blocked unless the article has passed validation."""
    allowed, reason = db.can_publish_article(article_id, as_draft=as_draft)
    if not allowed:
        return {
            "status": "blocked",
            "message": f"Publishing gate rejected this request: {reason}",
            "article_id": article_id,
        }

    article = db.get_article(article_id)
    target_status = "draft" if as_draft else "publish"

    client = WordPressClient()

    # Automatically generate & upload featured image banner
    featured_media_id = None
    media_res = None
    try:
        section = article.get("section") or "Cloud & DevOps"
        banner_bytes = generate_featured_banner(
            title=article["title"],
            section=section,
            output_path=f"data/articles/{article['slug']}-banner.png",
        )
        media_res = client.upload_media(
            image_bytes=banner_bytes,
            filename=f"{article['slug']}-banner.png",
            mime_type="image/png",
            alt_text=f"Featured banner for {article['title']}",
        )
        featured_media_id = media_res.get("media_id")
    except Exception as e:
        # Non-fatal fallback: publishing should proceed even if image generation encounters an issue
        pass

    wp_res = client.create_post(
        title=article["title"],
        slug=article["slug"],
        content_html=article["content_html"],
        status=target_status,
        excerpt=article.get("meta_description"),
        featured_media_id=featured_media_id,
    )

    pub_id = db.record_publication(
        article_id=article_id,
        site_id=article["site_id"],
        remote_post_id=wp_res.get("remote_id"),
        remote_url=wp_res.get("link"),
        status="DRAFT" if as_draft else "PUBLISHED",
    )

    return {
        "status": "success",
        "publication_id": pub_id,
        "article_id": article_id,
        "remote_post_id": wp_res.get("remote_id"),
        "remote_url": wp_res.get("link"),
        "featured_media_id": featured_media_id,
        "featured_media_url": media_res.get("source_url") if media_res else None,
        "wordpress_status": wp_res.get("status"),
        "dry_run": wp_res.get("dry_run", False),
    }


@mcp.tool()
def verify_publication(article_id: int) -> Dict[str, Any]:
    """Verify live status and content fidelity of a published article."""
    pub = db.get_publication(article_id)
    if not pub:
        return {"status": "error", "message": f"No publication record found for article {article_id}."}

    client = WordPressClient()
    wp_res = client.verify_post(pub["remote_post_id"])
    return {
        "status": "verified" if wp_res.get("verified") else "failed",
        "article_id": article_id,
        "remote_post_id": pub["remote_post_id"],
        "details": wp_res,
    }



def main():
    """Run the MCP server over stdio."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
