# AI Publisher - Development Log

## 2026-11-06

### What was built
- Initialized Git repository on `main` branch.
- Created project scaffolding according to repository layout plan:
  - `publisher_mcp/` package structure (`tools`, `database`, `validation`, `integrations`).
  - `.gitignore`, `pyproject.toml`, `.env.example`.
  - `docs/` (`AGENT_ROLE.md`, `EDITORIAL_POLICY.md`, `PUBLISHING_WORKFLOW.md`, `LOG.md`) and `tests/`.
- Completed Milestone 1 (Environment setup): Python 3.13 venv created, dependencies installed, pytest verified.
- Completed Milestone 2 (Agent capability test): Tested `agy -p` headless execution connecting to `publisher` MCP server and invoking `ping` tool successfully.
- Completed Milestone 3 (MCP skeleton + SQLite): Built SQLite data models (`schema.sql` and `db.py`) covering sites, topics, research, articles, versions, validations, and publications. Built state tools.
- Completed Milestone 4 (Validation + publishing gate): Implemented `ArticleValidator` in `engine.py` (prohibiting bad tags, YMYL keywords, h1 tags, requiring verified sources and metadata). Added strict gate blocking `publish_article` unless state is `APPROVED`.
- Completed Milestone 5 Foundation (WordPress adapter): Built `WordPressClient` in `integrations/wordpress.py` with support for dry-run simulation and REST API authentication. End-to-end pipeline tested (12 unit and integration tests passing).
- Completed Milestone 6 (Workflow Orchestration): Built `PipelineOrchestrator` in `orchestrator.py` to drive discovery -> research -> writing -> validation -> draft publication. Added CLI commands for manual or cron execution.
- Completed Milestone 7 & 8 (VM Deployment & Scheduling): Created `scripts/setup_vm.sh`, `systemd/ai-publisher.service`, `systemd/ai-publisher.timer`, and comprehensive deployment documentation in `docs/VM_DEPLOYMENT.md`.
- Completed Milestone 9 (Guardrails & Limits): Enforced kill switch (`PUBLISHING_ENABLED`), dry-run mode, and daily rate limit checks (`MAX_POSTS_PER_DAY`) at the publishing gate. 15 unit and integration tests passing.

### What broke
- `mcp.server.fastmcp` was renamed in `mcp 2.x` to `mcp.server.mcpserver.MCPServer`. Resolved by using `MCPServer`.

### What was learned
- Antigravity CLI (`agy`) 1.5.2 seamlessly connects to stdio MCP servers configured via `agy mcp add`.
- Headless execution with `--dangerously-skip-permissions` enables automated pipeline operation.

## 2026-11-07

### What was built
- Executed the full production pipeline end-to-end:
  - Topic discovery: Created topic 1 ("Migrating from Ingress-NGINX to Kubernetes Gateway API").
  - Web research: Stored 5 verified technical sources and extracted evidence in SQLite.
  - Synthesis: Drafted an 808-word production migration guide with manifests and CLI workflows.
  - Deterministic validation: Evaluated metadata, HTML hygiene, and research citations (passed 4/4 checks). State transitioned to `APPROVED`.
  - Publishing gate: Created WordPress draft publication (`simulated-wp-999`) in dry-run mode. State transitioned to `DRAFTED`.
  - Publication verification: Successfully verified post integrity via `verify_publication`.
- Verified SQLite persistence: State survived external CLI quota limitations without data loss.

### What was learned
- Separating AI reasoning from deterministic Python gates ensures that even when an LLM reaches quota or fails mid-stream, work is preserved and resumable at the exact state step.
