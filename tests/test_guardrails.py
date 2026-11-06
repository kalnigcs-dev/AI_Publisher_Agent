import pytest
from pathlib import Path
from publisher_mcp.database import db
from publisher_mcp.server import publish_article


@pytest.fixture
def guardrail_db(tmp_path: Path, monkeypatch):
    test_db = str(tmp_path / "guardrail.db")
    monkeypatch.setenv("SQLITE_DB_PATH", test_db)
    monkeypatch.setenv("DRY_RUN", "true")
    monkeypatch.setenv("PUBLISHING_ENABLED", "false")
    monkeypatch.setenv("MAX_POSTS_PER_DAY", "1")
    db.init_db(test_db)

    site_id = db.create_site(
        slug="guardrail-site",
        name="Guardrail Site",
        url="https://example.com",
        niche="Security",
        db_path=test_db,
    )
    topic_id = db.register_topic(
        site_id=site_id,
        title="Security Fundamentals in Python",
        slug="security-fundamentals-python",
        target_keyword="python security",
        db_path=test_db,
    )
    db.save_research_source(
        topic_id=topic_id,
        url="https://owasp.org",
        title="OWASP",
        db_path=test_db,
    )
    art = db.save_article(
        topic_id=topic_id,
        site_id=site_id,
        title="Security Fundamentals in Python",
        slug="security-fundamentals-python",
        content_html="<h2>Introduction</h2><p>" + "Security best practices " * 50 + "</p>",
        meta_description="A guide to security fundamentals and defensive programming in Python.",
        db_path=test_db,
    )
    # Validate and approve article
    db.record_validation_result(
        article_id=art["article_id"],
        version_id=art["version_id"],
        passed=True,
        checks_run=["metadata", "html"],
        errors=[],
        warnings=[],
        db_path=test_db,
    )
    return test_db, art["article_id"]


def test_kill_switch_blocks_live_publishing(guardrail_db, monkeypatch):
    test_db, article_id = guardrail_db
    monkeypatch.setenv("PUBLISHING_ENABLED", "false")

    # Live publishing should be BLOCKED by kill switch
    res = publish_article(article_id=article_id, as_draft=False)
    assert res["status"] == "blocked"
    assert "kill switch" in res["message"]

    # Draft publication should still be permitted
    draft_res = publish_article(article_id=article_id, as_draft=True)
    assert draft_res["status"] == "success"


def test_daily_rate_limit_blocks_excessive_posts(guardrail_db, monkeypatch):
    test_db, article1_id = guardrail_db
    monkeypatch.setenv("MAX_POSTS_PER_DAY", "1")

    # First post succeeds (draft)
    res1 = publish_article(article_id=article1_id, as_draft=True)
    assert res1["status"] == "success"

    # Create and approve a second distinct article for the same site
    art2 = db.save_article(
        topic_id=1,
        site_id=1,
        title="Second Article For Site",
        slug="second-article-for-site",
        content_html="<h2>Second Header</h2><p>" + "Second content words " * 50 + "</p>",
        meta_description="A second valid article to test the daily rate limit enforcement.",
        db_path=test_db,
    )
    article2_id = art2["article_id"]
    db.record_validation_result(
        article_id=article2_id,
        version_id=art2["version_id"],
        passed=True,
        checks_run=["metadata", "html"],
        errors=[],
        warnings=[],
        db_path=test_db,
    )

    # Second post on the same day exceeds limit (1/1)
    res2 = publish_article(article_id=article2_id, as_draft=True)
    assert res2["status"] == "blocked"
    assert "Daily publishing limit" in res2["message"]

