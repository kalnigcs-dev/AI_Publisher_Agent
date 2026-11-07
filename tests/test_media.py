import pytest
from pathlib import Path
from publisher_mcp.integrations.media import generate_featured_banner, generate_architecture_diagram_svg
from publisher_mcp.integrations.wordpress import WordPressClient


def test_generate_featured_banner(tmp_path: Path):
    banner_file = tmp_path / "test_banner.png"
    banner_bytes = generate_featured_banner(
        title="Deploying High-Performance Kubernetes Clusters",
        section="Cloud & DevOps",
        output_path=str(banner_file),
    )
    assert len(banner_bytes) > 0
    assert banner_file.exists()
    assert banner_file.stat().st_size > 0


def test_generate_svg_architecture_diagram():
    svg = generate_architecture_diagram_svg(
        title="Request Flow",
        stages=["Client", "Gateway", "Service"],
    )
    assert "<svg" in svg
    assert "</svg>" in svg
    assert "Client" in svg
    assert "Gateway" in svg
    assert "Service" in svg


def test_wordpress_client_media_upload_dry_run():
    client = WordPressClient()
    res = client.upload_media(
        image_bytes=b"dummy-image-bytes",
        filename="header.png",
        mime_type="image/png",
        alt_text="Test banner",
    )
    assert res["dry_run"] is True
    assert res["media_id"] == 888
    assert "header.png" in res["source_url"]


def test_wordpress_client_post_with_featured_media():
    client = WordPressClient()
    res = client.create_post(
        title="Article With Media",
        slug="article-with-media",
        content_html="<p>Body</p>",
        featured_media_id=888,
    )
    assert res["dry_run"] is True
    assert res["featured_media"] == 888
