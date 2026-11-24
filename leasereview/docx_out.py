"""Write the issues list as a Word document, the format a lawyer sends to the other side."""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.shared import Pt, RGBColor

from .guardrails import Item

GREY = RGBColor(0x5F, 0x5B, 0x52)


def _cell(cell, text: str, bold: bool = False, size: int = 9, color: RGBColor | None = None) -> None:
    cell.text = ""
    run = cell.paragraphs[0].add_run(text)
    run.bold = bold
    run.font.size = Pt(size)
    if color is not None:
        run.font.color.rgb = color


def _quote_text(item: Item) -> str:
    if not item.quotes:
        return ""
    return "\n".join(f"“{x.text}”" for x in item.quotes)


def write(items: list[Item], lease_title: str, playbook_name: str, path: str | Path) -> Path:
    doc = Document()
    section = doc.sections[0]
    section.orientation = WD_ORIENT.LANDSCAPE
    section.page_width, section.page_height = section.page_height, section.page_width
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(10)

    doc.add_heading("Lease issues list", level=1)
    meta = doc.add_paragraph()
    meta.add_run(lease_title).bold = True
    meta.add_run(
        f"\nRead against: {playbook_name}\nFirst draft for lawyer review. Not sent to the other side until a lawyer approves it."
    )

    rows = [i for i in items if i.kind in ("issue", "check")]
    doc.add_heading(f"Issues and checks ({len(rows)})", level=2)
    table = doc.add_table(rows=1, cols=6)
    table.style = "Table Grid"
    for c, h in zip(
        table.rows[0].cells, ["#", "Section", "Topic", "The lease says", "Our position", "Requested change"], strict=True
    ):
        _cell(c, h, bold=True)
    for n, item in enumerate(rows, 1):
        cells = table.add_row().cells
        _cell(cells[0], str(n))
        _cell(cells[1], ", ".join(item.sections) or "Not found")
        _cell(cells[2], f"{item.topic}\n{item.severity}" + ("\nCHECK" if item.kind == "check" else ""), bold=False)
        said = _quote_text(item) or item.lease_says or "The lease does not address this."
        _cell(cells[3], said)
        _cell(cells[4], item.standard)
        reply = item.proposed_response if item.kind == "issue" else " ".join(item.reasons)
        _cell(cells[5], reply, color=GREY if item.kind == "check" else None)

    ok = [i for i in items if i.kind == "consistent"]
    if ok:
        doc.add_heading(f"Consistent with our positions ({len(ok)})", level=2)
        for item in ok:
            p = doc.add_paragraph(style="List Bullet")
            p.add_run(f"{item.topic} ({', '.join(item.sections) or 'section not stated'}): ").bold = True
            p.add_run(item.lease_says)

    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    doc.save(out)
    return out
