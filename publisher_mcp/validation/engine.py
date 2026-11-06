"""Validation engine enforcing editorial rules and publishing gates."""

import re
from typing import Any, Dict, List, Optional
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field

# High-risk YMYL forbidden keywords (unless explicitly permitted by site profile)
DEFAULT_RESTRICTED_KEYWORDS = [
    "cure for cancer",
    "buy prescription drugs",
    "guaranteed returns",
    "crypto giveaway",
    "legal advice",
    "medical diagnosis",
    "kill yourself",
    "insider trading",
    "credit repair hack",
]

FORBIDDEN_TAGS = {"script", "style", "iframe", "object", "embed", "form", "input", "button"}


class ValidationReport(BaseModel):
    passed: bool
    checks_run: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)


def validate_metadata(
    title: str,
    slug: str,
    meta_description: Optional[str],
    report: ValidationReport,
) -> None:
    report.checks_run.append("metadata_check")

    # Title check
    if not title or len(title.strip()) < 10:
        report.errors.append("Article title must be at least 10 characters long.")
    elif len(title.strip()) > 120:
        report.warnings.append("Article title exceeds recommended SEO length (120 chars).")

    # Slug check
    if not slug or not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", slug):
        report.errors.append("Slug must be non-empty, lowercase alphanumeric with hyphen delimiters (e.g., 'sample-post-slug').")

    # Meta description check
    if not meta_description or len(meta_description.strip()) < 50:
        report.errors.append("Meta description must be at least 50 characters long.")
    elif len(meta_description.strip()) > 170:
        report.warnings.append("Meta description exceeds 170 characters (search engines may truncate).")


def validate_html_structure(
    content_html: str,
    min_word_count: int,
    report: ValidationReport,
) -> None:
    report.checks_run.append("html_structure_check")

    if not content_html or not content_html.strip():
        report.errors.append("Article HTML content cannot be empty.")
        return

    soup = BeautifulSoup(content_html, "html.parser")

    # Check for forbidden dangerous tags
    found_forbidden = [tag.name for tag in soup.find_all(FORBIDDEN_TAGS)]
    if found_forbidden:
        report.errors.append(f"Content contains prohibited HTML tags: {', '.join(set(found_forbidden))}")

    # Headings check
    h1_tags = soup.find_all("h1")
    if h1_tags:
        report.errors.append("Article body contains <h1> tags. Body headings should start at <h2> (post title is the <h1>).")

    h2_tags = soup.find_all("h2")
    if not h2_tags:
        report.errors.append("Article body must contain at least one <h2> section header.")

    # Word count calculation from text
    plain_text = soup.get_text(separator=" ", strip=True)
    words = plain_text.split()
    word_count = len(words)
    report.metrics["word_count"] = word_count

    if word_count < min_word_count:
        report.errors.append(
            f"Article word count ({word_count} words) is below the minimum required ({min_word_count} words)."
        )


def validate_restrictions(
    title: str,
    content_html: str,
    extra_forbidden_keywords: Optional[List[str]],
    report: ValidationReport,
) -> None:
    report.checks_run.append("restricted_topics_check")

    combined_text = f"{title} {content_html}".lower()
    all_restricted = list(DEFAULT_RESTRICTED_KEYWORDS)
    if extra_forbidden_keywords:
        all_restricted.extend(extra_forbidden_keywords)

    found_keywords = []
    for kw in all_restricted:
        if kw.lower() in combined_text:
            found_keywords.append(kw)

    if found_keywords:
        report.errors.append(
            f"Content violates editorial safety policy by containing restricted topic terms: {', '.join(found_keywords)}"
        )


def validate_sources(
    sources: List[Dict[str, Any]],
    report: ValidationReport,
) -> None:
    report.checks_run.append("sources_check")

    if not sources:
        report.errors.append("Article has no registered research sources. Every article must have at least one verified source.")
    else:
        verified_count = sum(1 for s in sources if s.get("is_verified", 1))
        report.metrics["sources_count"] = len(sources)
        report.metrics["verified_sources_count"] = verified_count
        if verified_count == 0:
            report.errors.append("None of the research sources have been verified.")


def validate_article_content(
    title: str,
    slug: str,
    content_html: str,
    meta_description: Optional[str] = None,
    sources: Optional[List[Dict[str, Any]]] = None,
    min_word_count: int = 150,
    extra_forbidden_keywords: Optional[List[str]] = None,
) -> ValidationReport:
    """Run all deterministic validation checks against an article draft."""
    report = ValidationReport(passed=True)

    validate_metadata(title=title, slug=slug, meta_description=meta_description, report=report)
    validate_html_structure(content_html=content_html, min_word_count=min_word_count, report=report)
    validate_restrictions(title=title, content_html=content_html, extra_forbidden_keywords=extra_forbidden_keywords, report=report)
    validate_sources(sources=sources or [], report=report)

    # Determine overall pass/fail
    report.passed = len(report.errors) == 0
    return report
