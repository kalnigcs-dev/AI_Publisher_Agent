# AI Publisher - Publishing Workflow & State Machine

## Overview

The publishing pipeline follows a strict unidirectional state machine. An article cannot reach the `PUBLISHED` state without passing deterministic validation and being stored in SQLite.

```
DISCOVERED -> RESEARCHED -> GENERATED -> VALIDATING -> APPROVED
   -> DRAFTED (on WordPress) -> PUBLISHED -> MONITORING
Failure: VALIDATION_FAILED | QUARANTINED | PUBLICATION_FAILED
```

---

## State Transition Details

### 1. `DISCOVERED`
- A topic is identified (via trend analysis, search queries, or content gap research).
- Agent calls `find_duplicate_topics(slug, keywords, site_id)` to ensure no collision or cannibalization.
- Agent calls `register_topic(site_id, title, target_keyword, rationale)`.

### 2. `RESEARCHED`
- Agent conducts web research using search tools.
- Agent saves validated sources and notes using `save_research(topic_id, sources, notes)`.
- Sources must be accessible and relevant.

### 3. `GENERATED`
- Agent drafts article title, slug, meta description, outline, and HTML content.
- Article is stored via `save_article(topic_id, title, slug, content_html, meta_desc)`.
- Initial article version is created.

### 4. `VALIDATING` / `APPROVED` / `VALIDATION_FAILED`
- Agent or pipeline runs `validate_article(article_id)`.
- Deterministic checks include:
  1. Valid, well-formed HTML (no unclosed tags, no dangerous tags like `<script>`).
  2. Required metadata present (title, meta description length, slug format).
  3. Source links present and reachable.
  4. Content uniqueness & minimum word count.
  5. Forbidden topic keywords / YMYL policy check.
- If checks pass: state transitions to `APPROVED`.
- If checks fail: state transitions to `VALIDATION_FAILED` with structured error feedback for remediation.

### 5. `DRAFTED`
- `publish_article(article_id, as_draft=True)` is called.
- The server (NOT the agent directly) speaks to WordPress REST API using configured credentials.
- WordPress post ID and draft URL are recorded in `publications` table.

### 6. `PUBLISHED` & `MONITORING`
- Once human review passes (during Milestone 6) or automated guardrails pass (Milestone 9), the post status transitions to `publish`.
- `verify_publication(article_id)` re-fetches the live URL and confirms content fidelity.
- Performance metrics (traffic, indexing status) are monitored over time.
