"""Build a clean Word document from the generated social drafts."""

from __future__ import annotations

from io import BytesIO
from typing import Any

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor


def build_word_document(article: dict[str, str], drafts: dict[str, Any]) -> bytes:
    document = Document()
    section = document.sections[0]
    section.top_margin = Inches(0.7)
    section.bottom_margin = Inches(0.7)
    section.left_margin = Inches(0.85)
    section.right_margin = Inches(0.85)

    normal = document.styles["Normal"]
    normal.font.name = "Aptos"
    normal.font.size = Pt(10.5)
    normal.font.color.rgb = RGBColor(45, 52, 60)

    title = document.add_heading("Content Repurposing Pack", level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.LEFT
    subtitle = document.add_paragraph(article.get("title", "Untitled article"))
    subtitle.style = "Subtitle"
    document.add_paragraph(f"Source: {article.get('url', '')}")
    document.add_paragraph("Review each draft before publishing. Check facts, tone and platform limits.")

    document.add_heading("X / Twitter thread", level=1)
    for post in drafts["x_thread"]:
        document.add_paragraph(post, style="List Number")

    document.add_heading("LinkedIn post", level=1)
    for paragraph in drafts["linkedin_post"].split("\n"):
        if paragraph.strip():
            document.add_paragraph(paragraph.strip())

    document.add_heading("Instagram caption", level=1)
    for paragraph in drafts["instagram_caption"].split("\n"):
        if paragraph.strip():
            document.add_paragraph(paragraph.strip())

    document.add_paragraph()
    footer = document.add_paragraph("Created with Week 2 Content Repurposer")
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer.runs[0].italic = True
    footer.runs[0].font.size = Pt(8)
    footer.runs[0].font.color.rgb = RGBColor(110, 118, 128)

    buffer = BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def build_markdown_document(article: dict[str, str], drafts: dict[str, Any]) -> bytes:
    lines = [
        "# Content Repurposing Pack",
        "",
        f"**Source article:** [{article.get('title', 'Untitled article')}]({article.get('url', '')})",
        "",
        "> Review each draft before publishing. Check facts, tone and platform limits.",
        "",
        "## X / Twitter thread",
        "",
    ]
    lines.extend(f"{index}. {post}" for index, post in enumerate(drafts["x_thread"], start=1))
    lines.extend(["", "## LinkedIn post", "", drafts["linkedin_post"], "", "## Instagram caption", "", drafts["instagram_caption"], ""])
    return "\n".join(lines).encode("utf-8")
