"""Automated media and visual assets generator for AI Publisher."""

import io
import textwrap
from pathlib import Path
from typing import List, Optional
from PIL import Image, ImageDraw, ImageFont


# Section color themes (RGB)
SECTION_COLORS = {
    "Artificial Intelligence": (147, 51, 234),     # Purple
    "Cloud & DevOps": (14, 165, 233),              # Sky Blue
    "Software Engineering": (16, 185, 129),        # Emerald Green
    "Hardware & Systems": (245, 158, 11),          # Amber / Orange
    "general": (59, 130, 246),                     # Blue
}


def generate_featured_banner(
    title: str,
    section: str = "Cloud & DevOps",
    brand_name: str = "CoreTech Digest",
    output_path: Optional[str] = None,
) -> bytes:
    """Generate a 1200x630 high-resolution featured banner suitable for Google Discover and social preview."""
    width = 1200
    height = 630

    # Base dark gradient background
    accent_color = SECTION_COLORS.get(section, SECTION_COLORS["general"])
    image = Image.new("RGB", (width, height), (15, 23, 42))  # Slate 900 base
    draw = ImageDraw.Draw(image)

    # Draw subtle background glow / accents
    glow_color = (
        int(accent_color[0] * 0.15),
        int(accent_color[1] * 0.15),
        int(accent_color[2] * 0.15),
    )
    draw.rounded_rectangle([40, 40, width - 40, height - 40], radius=24, outline=glow_color, width=2)
    draw.rectangle([0, 0, width, 8], fill=accent_color)  # Top highlight bar

    # Try loading default system font
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 44)
        font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    except Exception:
        font_large = ImageFont.load_default()
        font_medium = font_large
        font_small = font_large

    # 1. Section Badge
    badge_text = f"  {section.upper()}  "
    draw.rounded_rectangle([80, 80, 80 + len(badge_text) * 12 + 20, 120], radius=8, fill=accent_color)
    draw.text((90, 92), badge_text, fill=(255, 255, 255), font=font_medium)

    # 2. Main Title (Word-wrapped)
    wrapped_lines = textwrap.wrap(title, width=32)
    y_offset = 180
    for line in wrapped_lines[:4]:  # Max 4 lines
        draw.text((80, y_offset), line, fill=(248, 250, 252), font=font_large)
        y_offset += 64

    # 3. Footer Branding
    footer_text = f"{brand_name}  •  Technical Reference & Guide"
    draw.text((80, height - 90), footer_text, fill=(148, 163, 184), font=font_small)

    # Export to bytes
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    image_bytes = buffer.getvalue()

    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "wb") as f:
            f.write(image_bytes)

    return image_bytes


def generate_architecture_diagram_svg(
    title: str,
    stages: List[str],
    description: Optional[str] = None,
) -> str:
    """Generate clean, scalable inline SVG architecture diagram for technical articles."""
    svg_boxes = ""
    box_width = 220
    box_height = 80
    gap = 50
    start_x = 40
    start_y = 70

    for i, stage in enumerate(stages):
        x = start_x + i * (box_width + gap)
        svg_boxes += f"""
        <g transform="translate({x}, {start_y})">
            <rect width="{box_width}" height="{box_height}" rx="10" fill="#1e293b" stroke="#38bdf8" stroke-width="2" />
            <text x="{box_width / 2}" y="{box_height / 2 + 5}" fill="#f8fafc" font-size="14" font-weight="bold" font-family="system-ui, sans-serif" text-anchor="middle">{stage}</text>
        </g>
        """
        # Arrow connecting boxes
        if i < len(stages) - 1:
            arrow_x = x + box_width
            svg_boxes += f"""
            <line x1="{arrow_x + 8}" y1="{start_y + box_height / 2}" x2="{arrow_x + gap - 8}" y2="{start_y + box_height / 2}" stroke="#94a3b8" stroke-width="2" marker-end="url(#arrow)" />
            """

    total_width = start_x * 2 + len(stages) * box_width + (len(stages) - 1) * gap
    total_height = start_y + box_height + 40

    svg = f"""<svg viewBox="0 0 {total_width} {total_height}" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto;margin:24px 0;background:#0f172a;border-radius:12px;padding:16px;">
    <defs>
        <marker id="arrow" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#94a3b8" />
        </marker>
    </defs>
    <text x="40" y="36" fill="#38bdf8" font-size="16" font-weight="bold" font-family="system-ui, sans-serif">{title}</text>
    {svg_boxes}
</svg>"""
    return svg
