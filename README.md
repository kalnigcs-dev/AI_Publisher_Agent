# AI Publisher Agent

[![CI Tests](https://img.shields.io/badge/tests-19%20passed-brightgreen.svg)]()
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue.svg)]()
[![Protocol](https://img.shields.io/badge/protocol-MCP%202.x-orange.svg)]()
[![Integration](https://img.shields.io/badge/integration-WordPress%20REST%20API-informational.svg)]()
[![License](https://img.shields.io/badge/license-MIT-green.svg)]()

> **An autonomous, quality-gated technical publishing engine.** Powered by the **Model Context Protocol (MCP)**, **Antigravity CLI (`agy`)**, and a deterministic Python validation gate, publishing to **WordPress** via its REST API.

---

## 1. Overview & Problem Statement

Autonomous content generation systems frequently suffer from hallucinated claims, poor search ranking penalties, broken markup, and out-of-control publishing loops. 

**AI Publisher Agent** solves this through a strict **separation of concerns**:
- **Non-Deterministic Cognitive Layer (AI Agent):** Discovers high-intent technical topics, gathers real-world web research, cites authoritative sources, synthesizes deep architectural guides, and generates SVG system diagrams.
- **Deterministic Code Layer (Python MCP Server):** Manages relational persistence in SQLite, runs uncompromising quality and HTML gates, enforces daily rate limits and kill switches, creates 1200×630px OpenGraph/Google Discover banner artwork, and securely gates all WordPress REST API calls.

```
                    +------------------------------------+
                    |       systemd Timer / Scheduler    |
                    +-----------------+------------------+
                                      |
                                      v
                    +-----------------+------------------+
                    |  Antigravity CLI (agy / LLM)       |
                    |  - Topic Discovery & Research      |
                    |  - Synthesis & Inline SVG Diagrams |
                    +-----------------+------------------+
                                      | stdio (MCP Protocol)
                                      v
                    +-----------------+------------------+
                    |       Publisher MCP Server         |
                    |  +------------------------------+  |
                    |  | SQLite Relational State      |  |
                    |  +------------------------------+  |
                    |  | Deterministic Quality Gate   |  |
                    |  +------------------------------+  |
                    |  | Automated Pillow Media Engine|  |
                    |  +------------------------------+  |
                    |  | WordPress REST API Client    |  |
                    +-----------------+------------------+
                                      | HTTPS / Basic Auth (App Password)
                                      v
                    +-----------------+------------------+
                    |    WordPress Target (Draft Post)   |
                    +------------------------------------+
```

---

## 2. Core Principles & Guardrails

1. **Deterministic Gatekeeper:** The LLM never holds direct publishing credentials. Posts can **only** be published if their status in SQLite is `APPROVED` by the deterministic validator.
2. **Strict Editorial Standards (Anti-YMYL):** Zero tolerance for medical, legal, financial advice, or breaking news. The system targets specialized, high-CPC technical fields:
   - **Artificial Intelligence** (LLMs, vLLM, DeepSeek, Agentic Workflows)
   - **Cloud & DevOps** (Kubernetes, Gateway API, Ingress, Observability)
   - **Software Engineering** (Distributed systems, async Python, architecture)
   - **Hardware & Systems** (Edge computing, local acceleration)
3. **Evidence-Backed Sourcing:** Articles must reference real research URLs and cite verified technical specifications.
4. **Rich Visual Assets:** Every article is provisioned with:
   - A generated 1200×630px OpenGraph banner formatted for Google Discover.
   - Inline SVG architecture/flow diagrams embedded directly in the content.
5. **Zero Budget Footprint:** Runs on free Google Gemini tier via Antigravity CLI and Always-Free Oracle/Ubuntu cloud VMs.

---

## 3. Article State Machine

Articles advance through discrete, irreversible states stored in SQLite:

```
[DISCOVERED] ──> [RESEARCHED] ──> [GENERATED] ──> [VALIDATING]
                                                        │
                      ┌─────────────────────────────────┴─────────────────┐
                      ▼                                                   ▼
                [APPROVED]                                        [VALIDATION_FAILED]
                      │                                                   │
                      ▼                                                   ▼
                  [DRAFTED] (WordPress REST API)                     [QUARANTINED]
                      │
                      ▼
                 [PUBLISHED]
```

- Any failure during validation immediately halts the pipeline and transitions the article to `VALIDATION_FAILED` or `QUARANTINED`.
- Quota exhaustion or unexpected API errors trigger non-destructive retries; all state is preserved in SQLite across sessions.

---

## 4. MCP Server Tools

The custom MCP server exposes 14 tools to the agent:

| Category | Tool | Description |
|---|---|---|
| **System** | `ping` | Health check probe. |
| | `get_system_status` | Runtime environment, database connectivity, and version info. |
| **Site Management** | `list_sites` | Enumerate configured sites and editorial policies. |
| | `get_site_profile` | Retrieve niche, audience, and editorial constraints. |
| | `register_site` | Register a new target publication site. |
| **Topic Research** | `find_duplicate_topics` | Semantic/slug collision check against past articles. |
| | `register_topic` | Register a new proposed topic for development. |
| | `save_research` | Persist research URLs, key facts, and verified citations. |
| | `get_research` | Retrieve stored research notes for an article. |
| **Draft & State** | `save_article` | Save content, versions, meta descriptions, and tags. |
| | `get_article` | Retrieve full article state and version history. |
| **Quality & Gate** | `validate_article` | Execute deterministic checks (word count, structure, YMYL, HTML). |
| | `publish_article` | Upload media, attach featured banner, and push draft to WordPress. |
| | `verify_publication` | Fetch post from WordPress and verify parity with database record. |

---

## 5. Repository Structure

```
AI_Publisher_Agent/
├── publisher_mcp/                  # Core MCP Server & Pipeline Engine
│   ├── database/                   # SQLite persistence layer
│   │   ├── db.py                   # Data access methods & queries
│   │   ├── schema.sql              # Relational schema (8 tables)
│   │   └── seed.py                 # Initial site & section seeder
│   ├── integrations/               # External service adapters
│   │   ├── wordpress.py            # WordPress REST API client
│   │   └── media.py                # Pillow banner generator & SVG engine
│   ├── validation/                 # Quality gate
│   │   └── engine.py               # HTML, YMYL, header & source validator
│   ├── orchestrator.py             # CLI runner & step coordinator
│   └── server.py                   # FastMCP / stdio tool endpoints
├── local_wordpress/                # Local testing environment
│   ├── docker-compose.yml          # WordPress + MariaDB compose stack
│   └── start.sh                    # Automated bridge-network runner
├── systemd/                        # Automated scheduling
│   ├── ai-publisher.service        # systemd user service definition
│   └── ai-publisher.timer          # Periodic timer (runs publishing cycle)
├── scripts/                        # Utility & deployment scripts
│   ├── setup_vm.sh                 # Cloud VM bootstrap script
│   └── run_production_pipeline_sample.py
├── docs/                           # Documentation
│   ├── EDITORIAL_POLICY.md         # Content quality & anti-spam guidelines
│   ├── PUBLISHING_WORKFLOW.md      # End-to-end pipeline walk-through
│   ├── VM_DEPLOYMENT.md            # Cloud VM & systemd deployment guide
│   └── LOG.md                      # Milestone & operational changelog
├── tests/                          # Automated Pytest suite (19 tests)
├── .env.example                    # Environment variable template
├── pyproject.toml                  # Python package configuration
└── README.md                       # Project documentation
```

---

## 6. Getting Started

### Prerequisites
- **Python 3.11+** (Python 3.12 or 3.13 recommended)
- **Git** & **SQLite3**
- **Docker** (optional, for local WordPress testing)
- **Antigravity CLI (`agy`)** installed and authenticated

### Installation

```bash
# 1. Clone repository
git clone git@github.com:kalnigcs-dev/AI_Publisher_Agent.git
cd AI_Publisher_Agent

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies in editable mode
pip install --upgrade pip
pip install -e ".[dev]"

# 4. Configure environment
cp .env.example .env
nano .env
```

### Environment Configuration (`.env`)

```ini
# Database
PUBLISHER_DB_PATH=data/publisher.db

# WordPress REST API
WP_URL=http://localhost:8080
WP_USERNAME=publisher_admin
WP_APP_PASSWORD=xxxx xxxx xxxx xxxx

# Operational Controls
DRY_RUN=false
PUBLISHING_ENABLED=true
MAX_POSTS_PER_DAY=3
LOG_LEVEL=INFO
```

---

## 7. Running the Pipeline

### Option A: Pipeline CLI Orchestrator

The built-in orchestrator can run individual stages or complete cycles:

```bash
# Initialize SQLite database
python -c "from publisher_mcp.database import db; db.init_db()"

# Inspect pipeline summary
python -m publisher_mcp.orchestrator --step summary

# Run an end-to-end cycle (Discover -> Research -> Write -> Validate -> Draft)
python -m publisher_mcp.orchestrator --step cycle

# Run individual steps
python -m publisher_mcp.orchestrator --step discover
python -m publisher_mcp.orchestrator --step research
python -m publisher_mcp.orchestrator --step write
python -m publisher_mcp.orchestrator --step validate
python -m publisher_mcp.orchestrator --step draft
```

### Option B: Autonomous Agent Execution (`agy`)

Register the MCP server with the Antigravity agent CLI:

```bash
# Register MCP server with agy
agy mcp add publisher -- "$PWD/.venv/bin/python" -m publisher_mcp.server

# Verify MCP connectivity
agy -p "Call get_system_status on publisher" --dangerously-skip-permissions

# Run autonomous publishing task
agy -p "Review pending topics in AI Publisher, conduct research, write and validate the next approved draft." --dangerously-skip-permissions
```

---

## 8. Local WordPress Testing (Docker)

To test end-to-end publishing locally without a live production site:

```bash
# Start local WordPress and MariaDB containers on port 8080
./local_wordpress/start.sh

# Open WordPress admin in browser
# URL: http://localhost:8080/wp-admin
# Username: test | Password: testpassword
```

> **Note on Application Passwords:**  
> When running WordPress over local HTTP, ensure `define('WP_ENVIRONMENT_TYPE', 'local');` is added near line 2 of `/var/www/html/wp-config.php` and Apache forwards Authorization headers (`CGIPassAuth On` in `.htaccess`). The `./local_wordpress/start.sh` script applies these configurations automatically.

---

## 9. VM Deployment & Automation

For unattended 24/7 operation on an Ubuntu Cloud VM (e.g., Oracle Cloud Always-Free tier):

```bash
# 1. Automated VM provisioning
bash scripts/setup_vm.sh

# 2. Configure user systemd service and timer
mkdir -p ~/.config/systemd/user
cp systemd/ai-publisher.service ~/.config/systemd/user/
cp systemd/ai-publisher.timer ~/.config/systemd/user/

# 3. Reload and enable timer
systemctl --user daemon-reload
systemctl --user enable --now ai-publisher.timer

# 4. Verify scheduled execution
systemctl --user list-timers
```

See [docs/VM_DEPLOYMENT.md](docs/VM_DEPLOYMENT.md) for complete details.

---

## 10. Test Suite

Run the full automated test suite covering database operations, deterministic validation, Pillow banner generation, guardrails, and pipeline orchestration:

```bash
.venv/bin/pytest tests/ -v
```

```
============================== 19 passed in 0.64s ==============================
```

---

## 11. License

MIT License. See [LICENSE](LICENSE) for details.
