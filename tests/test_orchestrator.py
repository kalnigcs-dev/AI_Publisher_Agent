import pytest
from pathlib import Path
from publisher_mcp.database import db
from publisher_mcp.orchestrator import AgentRunner, PipelineOrchestrator


class MockAgentRunner(AgentRunner):
    """Mock agent runner simulating agy tool execution against the database."""

    def __init__(self, db_path: str, site_id: int):
        self.db_path = db_path
        self.site_id = site_id
        self.prompts_received = []

    def run_prompt(self, prompt: str, timeout: int = 300) -> str:
        self.prompts_received.append(prompt)

        # Simulate Discover tool call
        if "register_topic" in prompt:
            db.register_topic(
                site_id=self.site_id,
                title="Building Scalable Microservices with Python",
                slug="building-scalable-microservices-python",
                target_keyword="python microservices",
                rationale="High developer demand",
                db_path=self.db_path,
            )
            return "Registered topic 'Building Scalable Microservices with Python'"

        # Simulate Research tool call
        if "save_research" in prompt:
            pending = db.get_pending_topic_for_research(self.site_id, db_path=self.db_path)
            if pending:
                db.save_research_source(
                    topic_id=pending["id"],
                    url="https://docs.python.org/3/library/asyncio.html",
                    title="Python Asyncio Documentation",
                    snippet="Official asyncio library docs covering concurrency.",
                    db_path=self.db_path,
                )
            return "Saved research sources"

        # Simulate Write tool call
        if "save_article" in prompt and "remediation" not in prompt.lower():
            pending = db.get_pending_topic_for_writing(self.site_id, db_path=self.db_path)
            if pending:
                valid_content = "<h2>Microservices Architecture in Python</h2>" + "<p>Python offers robust frameworks like FastAPI and asyncio for microservices. </p>" * 20
                db.save_article(
                    topic_id=pending["id"],
                    site_id=self.site_id,
                    title=pending["title"],
                    slug=pending["slug"],
                    content_html=valid_content,
                    meta_description="Comprehensive guide to architecting and deploying scalable Python microservices.",
                    db_path=self.db_path,
                )
            return "Saved article draft"

        # Simulate Remediation
        if "remediation" in prompt.lower() or "validation errors" in prompt.lower():
            return "Remediated article draft"

        return "OK"


@pytest.fixture
def mock_env(tmp_path: Path, monkeypatch):
    test_db = str(tmp_path / "orch_test.db")
    monkeypatch.setenv("SQLITE_DB_PATH", test_db)
    monkeypatch.setenv("DRY_RUN", "true")
    db.init_db(test_db)

    site_id = db.create_site(
        slug="dev-insights",
        name="Developer Insights",
        url="https://devinsights.io",
        niche="Software Engineering",
        editorial_rules={"min_word_count": 100},
        db_path=test_db,
    )
    return test_db, site_id


def test_orchestrator_full_cycle(mock_env):
    test_db, site_id = mock_env
    runner = MockAgentRunner(db_path=test_db, site_id=site_id)
    orchestrator = PipelineOrchestrator(agent_runner=runner, site_id=site_id)

    # 1. Topic Discovery
    res_disc = orchestrator.step_discover_topics()
    assert res_disc["status"] == "success"
    topics = db.list_topics(site_id=site_id, db_path=test_db)
    assert len(topics) == 1
    assert topics[0]["status"] == "DISCOVERED"

    # 2. Research Step
    res_res = orchestrator.step_research_topic()
    assert res_res["status"] == "success"
    topics = db.list_topics(site_id=site_id, db_path=test_db)
    assert topics[0]["status"] == "RESEARCHED"

    # 3. Write Step
    res_write = orchestrator.step_write_article()
    assert res_write["status"] == "success"
    topics = db.list_topics(site_id=site_id, db_path=test_db)
    assert topics[0]["status"] == "GENERATED"
    art = db.get_article_by_slug(site_id=site_id, slug=topics[0]["slug"], db_path=test_db) if hasattr(db, "get_article_by_slug") else db.get_article(1, db_path=test_db)
    assert art is not None
    assert art["status"] == "GENERATED"

    # 4. Validate Step
    res_val = orchestrator.step_validate_article()
    assert res_val["status"] == "success"
    assert res_val["validation"]["passed"] is True
    art_val = db.get_article(art["id"], db_path=test_db)
    assert art_val["status"] == "APPROVED"

    # 5. Draft Publication Step
    res_draft = orchestrator.step_draft_publication()
    assert res_draft["status"] == "success"
    art_draft = db.get_article(art["id"], db_path=test_db)
    assert art_draft["status"] == "DRAFTED"
    pub = db.get_publication(art["id"], db_path=test_db)
    assert pub is not None
    assert pub["status"] == "DRAFT"
