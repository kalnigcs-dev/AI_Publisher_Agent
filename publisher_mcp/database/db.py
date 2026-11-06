"""Database connection and repository operations for AI Publisher."""

import json
import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

DEFAULT_DB_PATH = os.getenv("SQLITE_DB_PATH", "data/publisher.db")
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def get_db_path(override_path: Optional[str] = None) -> Path:
    """Resolve database path, ensuring parent directory exists."""
    path = Path(override_path or os.getenv("SQLITE_DB_PATH", DEFAULT_DB_PATH))
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Obtain a SQLite connection with row factory configured."""
    path = get_db_path(db_path)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: Optional[str] = None) -> None:
    """Initialize database tables from schema.sql."""
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    with get_connection(db_path) as conn:
        conn.executescript(schema_sql)


# --- Site Management ---

def create_site(
    slug: str,
    name: str,
    url: str,
    niche: str,
    language: str = "en",
    editorial_rules: Optional[Dict[str, Any]] = None,
    db_path: Optional[str] = None,
) -> int:
    rules_json = json.dumps(editorial_rules or {})
    with get_connection(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO sites (slug, name, url, niche, language, editorial_rules)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (slug, name, url, niche, language, rules_json),
        )
        return cursor.lastrowid


def list_sites(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    with get_connection(db_path) as conn:
        rows = conn.execute("SELECT * FROM sites ORDER BY id ASC").fetchall()
        result = []
        for row in rows:
            d = dict(row)
            if d.get("editorial_rules"):
                try:
                    d["editorial_rules"] = json.loads(d["editorial_rules"])
                except Exception:
                    pass
            result.append(d)
        return result


def get_site_profile(site_id_or_slug: Any, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    with get_connection(db_path) as conn:
        if isinstance(site_id_or_slug, int) or (isinstance(site_id_or_slug, str) and site_id_or_slug.isdigit()):
            row = conn.execute("SELECT * FROM sites WHERE id = ?", (int(site_id_or_slug),)).fetchone()
        else:
            row = conn.execute("SELECT * FROM sites WHERE slug = ?", (str(site_id_or_slug),)).fetchone()
        if not row:
            return None
        d = dict(row)
        if d.get("editorial_rules"):
            try:
                d["editorial_rules"] = json.loads(d["editorial_rules"])
            except Exception:
                pass
        return d


# --- Topic Management ---

def register_topic(
    site_id: int,
    title: str,
    slug: str,
    target_keyword: str,
    rationale: Optional[str] = None,
    db_path: Optional[str] = None,
) -> int:
    with get_connection(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO topics (site_id, title, slug, target_keyword, rationale, status)
            VALUES (?, ?, ?, ?, ?, 'DISCOVERED')
            """,
            (site_id, title, slug, target_keyword, rationale),
        )
        return cursor.lastrowid


def find_duplicate_topics(
    site_id: int,
    query_slug: str,
    query_keyword: Optional[str] = None,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    with get_connection(db_path) as conn:
        query = """
            SELECT id, site_id, title, slug, target_keyword, status, created_at
            FROM topics
            WHERE site_id = ? AND (slug = ? OR (? IS NOT NULL AND target_keyword = ?))
        """
        rows = conn.execute(query, (site_id, query_slug, query_keyword, query_keyword)).fetchall()
        return [dict(r) for r in rows]


def get_topic(topic_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    with get_connection(db_path) as conn:
        row = conn.execute("SELECT * FROM topics WHERE id = ?", (topic_id,)).fetchone()
        return dict(row) if row else None


def update_topic_status(topic_id: int, status: str, db_path: Optional[str] = None) -> None:
    with get_connection(db_path) as conn:
        conn.execute(
            "UPDATE topics SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, topic_id),
        )


# --- Research Sources ---

def save_research_source(
    topic_id: int,
    url: str,
    title: Optional[str] = None,
    snippet: Optional[str] = None,
    is_verified: bool = True,
    db_path: Optional[str] = None,
) -> int:
    with get_connection(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO research_sources (topic_id, url, title, snippet, is_verified)
            VALUES (?, ?, ?, ?, ?)
            """,
            (topic_id, url, title, snippet, 1 if is_verified else 0),
        )
        # Advance topic status to RESEARCHED if still DISCOVERED
        conn.execute(
            "UPDATE topics SET status = 'RESEARCHED', updated_at = CURRENT_TIMESTAMP WHERE id = ? AND status = 'DISCOVERED'",
            (topic_id,),
        )
        return cursor.lastrowid


def get_research_sources(topic_id: int, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    with get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM research_sources WHERE topic_id = ? ORDER BY id ASC", (topic_id,)
        ).fetchall()
        return [dict(r) for r in rows]


# --- Article Management ---

def save_article(
    topic_id: int,
    site_id: int,
    title: str,
    slug: str,
    content_html: str,
    meta_description: Optional[str] = None,
    change_summary: Optional[str] = None,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    with get_connection(db_path) as conn:
        # Check if article already exists for this site and slug
        existing = conn.execute(
            "SELECT id FROM articles WHERE site_id = ? AND slug = ?", (site_id, slug)
        ).fetchone()

        if existing:
            article_id = existing["id"]
            # Get latest version number
            last_version = conn.execute(
                "SELECT MAX(version_num) as max_v FROM article_versions WHERE article_id = ?",
                (article_id,),
            ).fetchone()
            next_version = (last_version["max_v"] or 0) + 1

            # Insert version
            v_cursor = conn.execute(
                """
                INSERT INTO article_versions (article_id, version_num, content_html, change_summary)
                VALUES (?, ?, ?, ?)
                """,
                (article_id, next_version, content_html, change_summary or f"Version {next_version}"),
            )
            version_id = v_cursor.lastrowid

            # Update article
            conn.execute(
                """
                UPDATE articles
                SET title = ?, meta_description = ?, current_version_id = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (title, meta_description, version_id, article_id),
            )
        else:
            # Create article first
            a_cursor = conn.execute(
                """
                INSERT INTO articles (topic_id, site_id, title, slug, meta_description, status)
                VALUES (?, ?, ?, ?, ?, 'GENERATED')
                """,
                (topic_id, site_id, title, slug, meta_description),
            )
            article_id = a_cursor.lastrowid

            # Create version 1
            v_cursor = conn.execute(
                """
                INSERT INTO article_versions (article_id, version_num, content_html, change_summary)
                VALUES (?, 1, ?, ?)
                """,
                (article_id, content_html, change_summary or "Initial draft"),
            )
            version_id = v_cursor.lastrowid

            # Update current_version_id
            conn.execute(
                "UPDATE articles SET current_version_id = ? WHERE id = ?",
                (version_id, article_id),
            )

            # Update topic status to GENERATED
            conn.execute(
                "UPDATE topics SET status = 'GENERATED', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (topic_id,),
            )

        return {
            "article_id": article_id,
            "version_id": version_id,
            "title": title,
            "slug": slug,
        }


def get_article(article_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    with get_connection(db_path) as conn:
        row = conn.execute(
            """
            SELECT a.*, v.content_html, v.version_num, v.created_at as version_created_at
            FROM articles a
            LEFT JOIN article_versions v ON a.current_version_id = v.id
            WHERE a.id = ?
            """,
            (article_id,),
        ).fetchone()
        return dict(row) if row else None


def update_article_status(article_id: int, status: str, db_path: Optional[str] = None) -> None:
    with get_connection(db_path) as conn:
        conn.execute(
            "UPDATE articles SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, article_id),
        )


# --- Validation Management ---

def record_validation_result(
    article_id: int,
    version_id: int,
    passed: bool,
    checks_run: List[str],
    errors: List[str],
    warnings: List[str],
    db_path: Optional[str] = None,
) -> int:
    with get_connection(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO validation_results (article_id, version_id, passed, checks_run, errors, warnings)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                article_id,
                version_id,
                1 if passed else 0,
                json.dumps(checks_run),
                json.dumps(errors),
                json.dumps(warnings),
            ),
        )
        res_id = cursor.lastrowid
        new_status = "APPROVED" if passed else "VALIDATION_FAILED"
        conn.execute(
            "UPDATE articles SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (new_status, article_id),
        )
        return res_id


def get_latest_validation(article_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    with get_connection(db_path) as conn:
        row = conn.execute(
            """
            SELECT * FROM validation_results
            WHERE article_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (article_id,),
        ).fetchone()
        if not row:
            return None
        d = dict(row)
        for key in ("checks_run", "errors", "warnings"):
            if d.get(key):
                try:
                    d[key] = json.loads(d[key])
                except Exception:
                    pass
        return d


def get_today_publication_count(site_id: int, db_path: Optional[str] = None) -> int:
    with get_connection(db_path) as conn:
        row = conn.execute(
            """
            SELECT COUNT(*) as count FROM publications
            WHERE site_id = ? AND date(created_at) = date('now') AND status != 'FAILED'
            """,
            (site_id,),
        ).fetchone()
        return row["count"] if row else 0


def can_publish_article(
    article_id: int,
    as_draft: bool = True,
    db_path: Optional[str] = None,
) -> tuple[bool, str]:
    """Strict publishing gate: Only APPROVED articles with passing validation and within limits can be published."""
    article = get_article(article_id, db_path=db_path)
    if not article:
        return False, f"Article {article_id} not found."

    if article["status"] != "APPROVED":
        return False, f"Article {article_id} status is '{article['status']}', expected 'APPROVED'."

    latest_val = get_latest_validation(article_id, db_path=db_path)
    if not latest_val or not latest_val.get("passed"):
        return False, f"Article {article_id} has not passed deterministic validation."

    if latest_val.get("version_id") != article.get("current_version_id"):
        return False, "Validation record does not match current article version."

    # Kill switch guardrail for live publishing
    if not as_draft:
        publishing_enabled = os.getenv("PUBLISHING_ENABLED", "false").lower() in ("true", "1", "yes")
        if not publishing_enabled:
            return False, "Live publishing is disabled by kill switch (PUBLISHING_ENABLED=false). Only drafts are permitted."

    # Daily rate limit check
    site_id = article["site_id"]
    site = get_site_profile(site_id, db_path=db_path) or {}
    editorial_rules = site.get("editorial_rules") or {}
    max_daily = editorial_rules.get("max_posts_per_day", int(os.getenv("MAX_POSTS_PER_DAY", "1")))

    today_count = get_today_publication_count(site_id, db_path=db_path)
    if today_count >= max_daily:
        return False, f"Daily publishing limit ({today_count}/{max_daily}) reached for site {site_id}."

    return True, "Article passed validation gate and is authorized for publishing."


# --- Publication Management ---

def record_publication(
    article_id: int,
    site_id: int,
    remote_post_id: str,
    remote_url: str,
    status: str = "DRAFT",
    error_message: Optional[str] = None,
    db_path: Optional[str] = None,
) -> int:
    with get_connection(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO publications (article_id, site_id, remote_post_id, remote_url, status, error_message)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (article_id, site_id, remote_post_id, remote_url, status, error_message),
        )
        pub_id = cursor.lastrowid
        new_status = "DRAFTED" if status.upper() == "DRAFT" else "PUBLISHED"
        conn.execute(
            "UPDATE articles SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (new_status, article_id),
        )
        return pub_id


def get_publication(article_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    with get_connection(db_path) as conn:
        row = conn.execute(
            """
            SELECT * FROM publications
            WHERE article_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (article_id,),
        ).fetchone()
        return dict(row) if row else None


# --- Workflow Query Helpers ---

def list_topics(
    site_id: Optional[int] = None,
    status: Optional[str] = None,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    with get_connection(db_path) as conn:
        query = "SELECT * FROM topics WHERE 1=1"
        params = []
        if site_id is not None:
            query += " AND site_id = ?"
            params.append(site_id)
        if status is not None:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY id ASC"
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


def get_pending_topic_for_research(site_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM topics WHERE site_id = ? AND status = 'DISCOVERED' ORDER BY id ASC LIMIT 1",
            (site_id,),
        ).fetchone()
        return dict(row) if row else None


def get_pending_topic_for_writing(site_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM topics WHERE site_id = ? AND status = 'RESEARCHED' ORDER BY id ASC LIMIT 1",
            (site_id,),
        ).fetchone()
        return dict(row) if row else None


def get_pending_article_for_validation(site_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM articles WHERE site_id = ? AND status = 'GENERATED' ORDER BY id ASC LIMIT 1",
            (site_id,),
        ).fetchone()
        return dict(row) if row else None


def get_pending_article_for_draft(site_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM articles WHERE site_id = ? AND status = 'APPROVED' ORDER BY id ASC LIMIT 1",
            (site_id,),
        ).fetchone()
        return dict(row) if row else None


# --- Job History ---

def record_job_start(
    site_id: Optional[int],
    job_type: str,
    details: Optional[Dict[str, Any]] = None,
    db_path: Optional[str] = None,
) -> int:
    with get_connection(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO job_history (site_id, job_type, status, details, started_at)
            VALUES (?, ?, 'RUNNING', ?, CURRENT_TIMESTAMP)
            """,
            (site_id, job_type, json.dumps(details or {})),
        )
        return cursor.lastrowid


def record_job_end(
    job_id: int,
    status: str,
    details: Optional[Dict[str, Any]] = None,
    db_path: Optional[str] = None,
) -> None:
    with get_connection(db_path) as conn:
        conn.execute(
            """
            UPDATE job_history
            SET status = ?, details = ?, ended_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (status, json.dumps(details or {}), job_id),
        )


def get_pipeline_summary(site_id: Optional[int] = None, db_path: Optional[str] = None) -> Dict[str, Any]:
    with get_connection(db_path) as conn:
        where_clause = "WHERE site_id = ?" if site_id is not None else ""
        params = (site_id,) if site_id is not None else ()

        topics_count = conn.execute(
            f"SELECT status, count(*) as count FROM topics {where_clause} GROUP BY status", params
        ).fetchall()
        articles_count = conn.execute(
            f"SELECT status, count(*) as count FROM articles {where_clause} GROUP BY status", params
        ).fetchall()
        pubs_count = conn.execute(
            f"SELECT status, count(*) as count FROM publications {where_clause} GROUP BY status", params
        ).fetchall()

        return {
            "topics": {row["status"]: row["count"] for row in topics_count},
            "articles": {row["status"]: row["count"] for row in articles_count},
            "publications": {row["status"]: row["count"] for row in pubs_count},
        }



