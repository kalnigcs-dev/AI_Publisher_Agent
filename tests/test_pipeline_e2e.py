import pytest
from pathlib import Path
from publisher_mcp.database import db
from publisher_mcp.server import (
    register_site,
    register_topic,
    find_duplicate_topics,
    save_research,
    save_article,
    validate_article,
    publish_article,
    verify_publication,
)


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path: Path, monkeypatch):
    test_db = str(tmp_path / "e2e_test.db")
    monkeypatch.setenv("SQLITE_DB_PATH", test_db)
    monkeypatch.setenv("DRY_RUN", "true")
    db.init_db(test_db)
    return test_db


def test_full_pipeline_workflow():
    # 1. Register Site
    site_res = register_site(
        slug="cloud-insights",
        name="Cloud Insights",
        url="https://cloudinsights.io",
        niche="Cloud Computing",
        editorial_rules={"min_word_count": 100},
    )
    site_id = site_res["site_id"]
    assert site_id > 0

    # 2. Register Topic
    topic_res = register_topic(
        site_id=site_id,
        title="Serverless vs Edge Computing in 2026",
        slug="serverless-vs-edge-computing-2026",
        target_keyword="serverless vs edge computing",
        rationale="Growing query volume and clear technical audience.",
    )
    assert topic_res["status"] == "registered"
    topic_id = topic_res["topic_id"]

    # 3. Duplicate check prevents re-registering identical topic
    dupe_res = register_topic(
        site_id=site_id,
        title="Serverless vs Edge Computing in 2026 Clone",
        slug="serverless-vs-edge-computing-2026",
        target_keyword="serverless vs edge computing",
    )
    assert dupe_res["status"] == "rejected"

    # 4. Save Research
    res_saved = save_research(
        topic_id=topic_id,
        url="https://aws.amazon.com/serverless",
        title="AWS Serverless Overview",
        snippet="Serverless execution models and edge distribution.",
        is_verified=True,
    )
    assert res_saved["status"] == "saved"

    # 5. Save Invalid Article Draft (contains prohibited tag and <h1>)
    invalid_art = save_article(
        topic_id=topic_id,
        site_id=site_id,
        title="Serverless vs Edge Computing in 2026",
        slug="serverless-vs-edge-computing-2026",
        content_html="<h1>Invalid H1</h1><script>evil()</script><p>Too short.</p>",
        meta_description="Too short",
        change_summary="Bad draft",
    )
    art_id = invalid_art["article_id"]

    # 6. Validate Article -> Must Fail
    val_fail = validate_article(article_id=art_id)
    assert not val_fail["passed"]
    assert val_fail["new_status"] == "VALIDATION_FAILED"
    assert len(val_fail["errors"]) > 0

    # 7. Attempt Publish -> Must be BLOCKED by gate
    pub_blocked = publish_article(article_id=art_id, as_draft=True)
    assert pub_blocked["status"] == "blocked"
    assert "Publishing gate rejected" in pub_blocked["message"]

    # 8. Remediate Draft with high-quality, valid content
    valid_content = "<h2>Key Differences Between Serverless and Edge</h2>" + "<p>Modern distributed architectures leverage serverless for heavy computing and edge nodes for ultra-low latency. </p>" * 15
    fixed_art = save_article(
        topic_id=topic_id,
        site_id=site_id,
        title="Serverless vs Edge Computing in 2026: An Architecture Guide",
        slug="serverless-vs-edge-computing-2026",
        content_html=valid_content,
        meta_description="A technical comparison of serverless and edge computing architectures for cloud engineers in 2026.",
        change_summary="Fixed HTML tags, expanded depth, corrected metadata",
    )
    assert fixed_art["article_id"] == art_id

    # 9. Validate Remediated Draft -> Must PASS
    val_pass = validate_article(article_id=art_id)
    assert val_pass["passed"]
    assert val_pass["new_status"] == "APPROVED"
    assert len(val_pass["errors"]) == 0

    # 10. Attempt Publish -> Now SUCCEEDS
    pub_success = publish_article(article_id=art_id, as_draft=True)
    assert pub_success["status"] == "success"
    assert pub_success["publication_id"] > 0
    assert pub_success["dry_run"] is True

    # 11. Verify Publication
    ver_res = verify_publication(article_id=art_id)
    assert ver_res["status"] == "verified"
