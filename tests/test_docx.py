from docx import Document

from leasereview import docx_out, guardrails
from tests.test_guardrails import LEASE, review, row


def test_issues_list_lists_issues_and_checks_then_consistent(playbook, tmp_path):
    r = review(
        [
            row("assignment", "departs", ["consent shall not be unreasonably withheld"]),
            row("use", "consistent", ["solely for general, executive and administrative offices"]),
        ]
    )
    items = guardrails.apply(playbook, r, LEASE)
    path = docx_out.write(items, "Test lease", playbook.name, tmp_path / "issues.docx")
    doc = Document(str(path))
    table = doc.tables[0]
    assert len(table.rows) == 1 + 14  # header + 1 issue + 13 checks
    assert "consent shall not be unreasonably withheld" in table.rows[1].cells[3].text
    assert table.rows[1].cells[5].text == "fix it"
    text = "\n".join(p.text for p in doc.paragraphs)
    assert "Consistent with our positions (1)" in text
    assert "Not sent to the other side until a lawyer approves it" in text
