import pytest
from pathlib import Path
from publisher_mcp.database import db
from publisher_mcp.validation.engine import validate_article_content


@pytest.fixture
def temp_db(tmp_path: Path):
    db_file = str(tmp_path / "test_val.db")
    db.init_db(db_file)
    return db_file


def test_validation_catches_missing_sources():
    report = validate_article_content(
        title="Valid Title for Machine Learning",
        slug="valid-title-for-machine-learning",
        content_html="<h2>Overview</h2><p>" + "word " * 160 + "</p>",
        meta_description="A good description that is sufficiently long to pass the minimum character count check.",
        sources=[],  # No sources!
    )
    assert not report.passed
    assert any("no registered research sources" in err for err in report.errors)


def test_validation_catches_forbidden_html():
    report = validate_article_content(
        title="Testing Dangerous Script Tags",
        slug="testing-dangerous-script-tags",
        content_html="<h2>Header</h2><script>alert('xss');</script><p>" + "word " * 160 + "</p>",
        meta_description="A good description that is sufficiently long to pass the minimum character count check.",
        sources=[{"url": "https://example.com", "is_verified": 1}],
    )
    assert not report.passed
    assert any("prohibited HTML tags" in err for err in report.errors)


def test_validation_catches_h1_in_body():
    report = validate_article_content(
        title="Testing H1 in Body",
        slug="testing-h1-in-body",
        content_html="<h1>Disallowed H1</h1><p>" + "word " * 160 + "</p>",
        meta_description="A good description that is sufficiently long to pass the minimum character count check.",
        sources=[{"url": "https://example.com", "is_verified": 1}],
    )
    assert not report.passed
    assert any("<h1> tags" in err for err in report.errors)


def test_validation_catches_short_word_count():
    report = validate_article_content(
        title="Valid Title for Short Content",
        slug="valid-title-short-content",
        content_html="<h2>Section</h2><p>Too short text.</p>",
        meta_description="A good description that is sufficiently long to pass the minimum character count check.",
        sources=[{"url": "https://example.com", "is_verified": 1}],
        min_word_count=150,
    )
    assert not report.passed
    assert any("below the minimum required" in err for err in report.errors)


def test_validation_catches_restricted_ymyl_keywords():
    report = validate_article_content(
        title="Guaranteed Returns in Crypto",
        slug="guaranteed-returns-crypto",
        content_html="<h2>Section</h2><p>" + "word " * 160 + " guaranteed returns.</p>",
        meta_description="A good description that is sufficiently long to pass the minimum character count check.",
        sources=[{"url": "https://example.com", "is_verified": 1}],
    )
    assert not report.passed
    assert any("restricted topic terms" in err for err in report.errors)


def test_validation_gate_in_db(temp_db):
    site_id = db.create_site(
        slug="pilot",
        name="Pilot",
        url="https://pilot.local",
        niche="DevOps",
        db_path=temp_db,
    )
    topic_id = db.register_topic(
        site_id=site_id,
        title="Docker Container Best Practices",
        slug="docker-container-best-practices",
        target_keyword="docker best practices",
        db_path=temp_db,
    )
    db.save_research_source(
        topic_id=topic_id,
        url="https://docs.docker.com",
        title="Docker Docs",
        db_path=temp_db,
    )
    art = db.save_article(
        topic_id=topic_id,
        site_id=site_id,
        title="Docker Container Best Practices",
        slug="docker-container-best-practices",
        content_html="<h2>Introduction</h2><p>" + "Docker containerization " * 80 + "</p>",
        meta_description="Comprehensive guide covering Docker container best practices for DevOps teams.",
        db_path=temp_db,
    )
    article_id = art["article_id"]
    version_id = art["version_id"]

    # Before validation: Cannot publish (status is GENERATED)
    allowed, reason = db.can_publish_article(article_id, db_path=temp_db)
    assert not allowed
    assert "GENERATED" in reason

    # Record failed validation: Still cannot publish
    db.record_validation_result(
        article_id=article_id,
        version_id=version_id,
        passed=False,
        checks_run=["metadata_check"],
        errors=["Missing required field"],
        warnings=[],
        db_path=temp_db,
    )
    allowed, reason = db.can_publish_article(article_id, db_path=temp_db)
    assert not allowed
    assert "VALIDATION_FAILED" in reason

    # Record passing validation: Now publishing is allowed
    db.record_validation_result(
        article_id=article_id,
        version_id=version_id,
        passed=True,
        checks_run=["metadata_check", "html_structure_check", "sources_check"],
        errors=[],
        warnings=[],
        db_path=temp_db,
    )
    allowed, reason = db.can_publish_article(article_id, db_path=temp_db)
    assert allowed
    assert "authorized" in reason
