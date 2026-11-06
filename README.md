# AI Publisher

> Working title. An autonomous, quality-gated publishing system: an AI coding agent researches, writes and publishes blog articles to WordPress through a custom MCP server.

**Status:** In Progress (Milestones 1–4 implemented and verified).

---

## 1. Objective

Build a system that runs a blog (later several niche blogs) with minimal human involvement:

**Discover topic -> Research -> Write -> Validate -> Publish -> Measure -> Improve**

- **Brain:** Antigravity CLI (`agy`), running on an existing free Google account.
- **Hands:** a custom Python MCP server that gives the agent persistent state, validation and a controlled publishing path.
- **Destination:** WordPress sites.
- **Business goal:** organic search traffic, monetized later (e.g. Google AdSense). Revenue is a hypothesis, not a guarantee.
- **Personal goal:** understand every component well enough to maintain and reverse it.

## 2. Principles

1. **$0 until revenue justifies spending.** No paid LLM APIs, keyword tools or cloud services.
2. **Use AI for reasoning, code for everything deterministic.** Duplicate checks, HTML validation and publishing are plain Python.
3. **No publish without passing validation.** The agent cannot override a failed check.
4. **State lives in SQLite, not in the chat.** Work must survive quota limits and new sessions.
5. **Small, reversible steps.** One milestone at a time, committed to Git.
6. **Quality over volume.** One real niche, original value, sourced claims.

## 3. Architecture

```
Scheduler (systemd timer)
        |
Antigravity CLI (agent: reasoning, search, writing)
        |  MCP (stdio)
Publisher MCP server (Python)
   |-- SQLite (topics, research, articles, publications)
   |-- Validation engine
   |-- WordPress adapter (REST API)
        |
WordPress site(s)
```

**The agent already has:** web search/fetch, file access, a shell, a language model.
**We build only:** state tools, validation, the publishing gate.

### Key design rule: the publishing gate
If the agent can call a WordPress tool directly, it can skip validation. Therefore:
- `publish_article` lives in **our** server and calls WordPress itself.
- Direct WordPress publish tools are **not** given to the agent.
- `publish_article` takes an article ID and refuses unless the stored version passed validation.

## 4. Planned MCP tools (v1)

| Tool | Purpose |
|---|---|
| `list_sites` / `get_site_profile` | Niche, language, audience, editorial rules |
| `register_topic` | Save a proposed topic |
| `find_duplicate_topics` | Check overlap with existing topics and posts |
| `save_research` | Store sources and extracted evidence |
| `save_article` | Store article content (versioned) |
| `get_article` | Retrieve an article and its state |
| `validate_article` | Deterministic checks (see below) |
| `publish_article` | Gated publish (draft first) |
| `verify_publication` | Re-fetch the post and confirm it matches |

**Validation checks (initial):** sources present and reachable, duplicate content, valid HTML, title/meta/slug/headings present, internal links resolve, topic not on the restricted list.

## 5. Article states

```
DISCOVERED -> RESEARCHED -> GENERATED -> VALIDATING -> APPROVED
   -> DRAFTED (on WordPress) -> PUBLISHED -> MONITORING
Failure: VALIDATION_FAILED | QUARANTINED | PUBLICATION_FAILED
```
No direct jump from `GENERATED` to `PUBLISHED`.

## 6. Initial data model (SQLite)

`sites`, `topics`, `research_sources`, `articles`, `article_versions`, `validation_results`, `publications`, `job_history`.
Every content row is tied to a `site_id`. Slugs are unique per site. Publishing jobs are idempotent.

## 7. Milestones

| # | Milestone | Status | Done when |
|---|---|---|---|
| M0 | Decisions made (section 9) | Open | Niche and WordPress hosting chosen |
| M1 | Environment | Completed | Python venv, Git, MCP SDK, `agy` working locally |
| M2 | Agent capability test | Completed | `agy` can use web search, connect to a local MCP server, and run headless (`agy -p`) |
| M3 | MCP skeleton + SQLite | Completed | State tools work across sessions |
| M4 | Validation + gate | Completed | Bad articles are blocked; tests prove it |
| M5 | WordPress adapter | In Progress | Draft creation and verification on a test site (dry-run adapter ready) |
| M6 | Workflow | Next | Topic -> research -> article -> draft, reviewed by a human |
| M7 | VM deployment | Queued | Same setup runs on the Oracle VM |
| M8 | Scheduling | Queued | systemd timer runs one job unattended |
| M9 | Autonomous publishing | Queued | Enabled on one site with limits and a kill switch |
| M10 | Analytics | Queued | Search Console data feeds improvements |

Develop and test on the local machine first, then move to the VM.

## 8. Repository layout (proposed)

```
ai-publisher/
|-- publisher_mcp/
|   |-- server.py
|   |-- tools/
|   |-- database/
|   |-- validation/
|   `-- integrations/wordpress.py
|-- docs/
|   |-- AGENT_ROLE.md
|   |-- EDITORIAL_POLICY.md
|   `-- PUBLISHING_WORKFLOW.md
|-- data/            # SQLite, gitignored
|-- tests/
|-- .agents/mcp_config.json
|-- .env.example
|-- .gitignore
|-- pyproject.toml
`-- README.md
```

## 9. Open decisions

- [ ] **Niche for the pilot site** (audience, search demand, room for original value)
- [ ] **WordPress hosting:** WordPress.com Free (testing only, no AdSense) vs self-hosted on the Oracle VM (needs a domain for AdSense)
- [ ] **Language(s)** for the first site
- [ ] **Topics that are off-limits** for autonomy (medical, legal, financial advice, breaking news)
- [ ] **Publishing limits** (max posts per day, per site)
- [ ] **Where the VM lives long-term:** trial shape ends ~early December; move to an Always Free A1 shape or upgrade to Pay As You Go

## 10. Constraints and risks

| Risk | Mitigation |
|---|---|
| Free-tier `agy` weekly quota | Small tasks, state in SQLite, quota-aware job limits |
| `agy` headless/auth on a server | Test in M2 before building on it |
| Low-quality or duplicate AI content hurts search and AdSense approval | Strict validation, one real niche, human review before autonomy |
| Prompt injection from web pages | Treat fetched content as data, never instructions; only the MCP server authorizes actions |
| Credentials leaked | `.env` and tokens gitignored, dedicated restricted WordPress user |
| Trial VM expires | Keep setup scripted and in Git so it can be rebuilt |
| Unproven assumptions (WordPress MCP unattended writes, AdSense approval, traffic) | Treat as tests, not facts |

## 11. Compliance notes

- Follow Google's people-first and spam policies: no mass-produced unoriginal pages, no fabricated experts or experiences.
- AdSense approval and revenue are not guaranteed. Never generate artificial traffic or clicks.
- Each site must have a genuine audience and purpose.

## 12. Setup (to be filled in as built)

```bash
# M1
git clone <repo> && cd ai-publisher
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
cp .env.example .env   # add site settings, never commit
```

## 13. Working log

Keep a short dated log in `docs/LOG.md`: what was built, what broke, what was learned.
