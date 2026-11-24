import pytest

from leasereview.playbook import load


def test_sample_playbook_has_15_positions(playbook):
    assert len(playbook.positions) == 15
    assert {p.severity for p in playbook.positions} <= {"critical", "major", "minor"}
    assert sum(p.severity == "critical" for p in playbook.positions) == 5


def test_duplicate_ids_rejected(tmp_path):
    f = tmp_path / "p.yml"
    row = "  - {id: a, topic: t, severity: major, standard: s, departs_if: d, response: r}\n"
    f.write_text("name: x\npositions:\n" + row + row)
    with pytest.raises(ValueError):
        load(f)


def test_bad_severity_rejected(tmp_path):
    f = tmp_path / "p.yml"
    f.write_text("name: x\npositions:\n  - {id: a, topic: t, severity: huge, standard: s, departs_if: d, response: r}\n")
    with pytest.raises(ValueError):
        load(f)


def test_fingerprint_changes_with_positions(playbook, tmp_path):
    import yaml

    from leasereview import pipeline

    data = yaml.safe_load(pipeline.PLAYBOOK.read_text())
    data["positions"][0]["standard"] += " Changed."
    f = tmp_path / "p.yml"
    f.write_text(yaml.safe_dump(data))
    assert load(f).fingerprint() != playbook.fingerprint()
