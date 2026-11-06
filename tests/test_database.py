import pytest
from pathlib import Path
from publisher_mcp.database.db import (
    init_db,
    create_site,
    list_sites,
    get_site_profile,
    register_topic,
    find_duplicate_topics,
    save_research_source,
    get_research_sources,
    save_article,
    get_article,
)


@pytest.fixture
def temp_db(tmp_path: Path):
    db_file = str(tmp_path / "test_publisher.db")
    init_db(db_file)
    return db_file


def test_site_lifecycle(temp_db):
    site_id = create_site(
        slug="tech-pilot",
        name="Tech Pilot Blog",
        url="https://techpilot.example.com",
        niche="Cloud Engineering",
        editorial_rules={"min_word_count": 800},
        db_path=temp_db,
    )
    assert site_id > 0

    sites = list_sites(db_path=temp_db)
    assert len(sites) == 1
    assert sites[0]["slug"] == "tech-pilot"
    assert sites[0]["editorial_rules"]["min_word_count"] == 800

    profile = get_site_profile("tech-pilot", db_path=temp_db)
    assert profile is not None
    assert profile["name"] == "Tech Pilot Blog"


def test_topic_and_duplicate_check(temp_db):
    site_id = create_site(
        slug="tech-pilot",
        name="Tech Pilot Blog",
        url="https://techpilot.example.com",
        niche="Cloud Engineering",
        db_path=temp_db,
    )

    t_id = register_topic(
        site_id=site_id,
        title="Deploying SQLite with Python",
        slug="deploying-sqlite-python",
        target_keyword="sqlite python",
        rationale="High developer interest",
        db_path=temp_db,
    )
    assert t_id > 0

    # Duplicate check by slug
    dupes = find_duplicate_topics(site_id, "deploying-sqlite-python", db_path=temp_db)
    assert len(dupes) == 1

    # Duplicate check by keyword
    dupes_kw = find_duplicate_topics(site_id, "other-slug", query_keyword="sqlite python", db_path=temp_db)
    assert len(dupes_kw) == 1

    # Non-duplicate
    none_dupe = find_duplicate_topics(site_id, "different-slug", query_keyword="kubernetes", db_path=temp_db)
    assert len(none_dupe) == 0


def test_research_and_article_versioning(temp_db):
    site_id = create_site(
        slug="tech-pilot",
        name="Tech Pilot Blog",
        url="https://techpilot.example.com",
        niche="Cloud Engineering",
        db_path=temp_db,
    )

    topic_id = register_topic(
        site_id=site_id,
        title="Modern MCP Servers",
        slug="modern-mcp-servers",
        target_keyword="mcp python",
        db_path=temp_db,
    )

    # Save research
    save_research_source(
        topic_id=topic_id,
        url="https://modelcontextprotocol.io",
        title="MCP Spec",
        snippet="Official Model Context Protocol documentation.",
        db_path=temp_db,
    )
    sources = get_research_sources(topic_id, db_path=temp_db)
    assert len(sources) == 1
    assert sources[0]["url"] == "https://modelcontextprotocol.io"

    # Save Article Draft v1
    res1 = save_article(
        topic_id=topic_id,
        site_id=site_id,
        title="Modern MCP Servers",
        slug="modern-mcp-servers",
        content_html="<p>Introduction to MCP servers.</p>",
        meta_description="A quick guide to MCP servers.",
        change_summary="Initial draft",
        db_path=temp_db,
    )
    article_id = res1["article_id"]
    assert article_id > 0

    art_v1 = get_article(article_id, db_path=temp_db)
    assert art_v1["version_num"] == 1
    assert "<p>Introduction to MCP servers.</p>" in art_v1["content_html"]

    # Save Article Draft v2 (same slug & site_id updates and creates new version)
    res2 = save_article(
        topic_id=topic_id,
        site_id=site_id,
        title="Modern MCP Servers - Complete Guide",
        slug="modern-mcp-servers",
        content_html="<p>Comprehensive guide to MCP servers with real code.</p>",
        meta_description="A comprehensive guide to MCP servers.",
        change_summary="Expanded content",
        db_path=temp_db,
    )
    assert res2["article_id"] == article_id

    art_v2 = get_article(article_id, db_path=temp_db)
    assert art_v2["version_num"] == 2
    assert "Comprehensive guide" in art_v2["content_html"]
