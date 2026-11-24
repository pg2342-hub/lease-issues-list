# lease-issues-list

[![CI](https://github.com/pg2342-hub/lease-issues-list/actions/workflows/ci.yml/badge.svg)](https://github.com/pg2342-hub/lease-issues-list/actions/workflows/ci.yml)

Demo page: https://pranavgudise.dev/lease-issues-list/ (pick a lease, read each issue with the clause in context, accept, reject or edit the requested change, and download the issues list as a Word file; no install needed)

Reviews a commercial office lease against a firm's standard positions and drafts the issues list a lawyer would send back to the other side: for every position, whether the lease departs from it, the section and the clause quoted word for word, and the requested change. A lawyer reviews every line before anything is sent.

## How it works

1. **Read.** One Claude call (`claude-opus-5-5`, structured output) reads the whole lease, riders included, against the playbook in `playbooks/landlord_office_ny.yml` and returns a call, quotes, section numbers and a requested change for each of the 15 positions.
2. **Check.** Code, not the model, decides what reaches the lawyer (`leasereview/guardrails.py`). Every quote is matched against the lease text after normalizing typography and line breaks. A quote that is not in the lease is removed. A call left with no verified quote, marked low confidence, about a point the lease never mentions, or skipped by the model becomes a **check** item instead of an issue. Nothing is dropped: every position ends up as an issue, a check or consistent.
3. **Draft.** The issues list is written as a Word document (`leasereview/docx_out.py`): issues and checks first, by severity, then the positions the lease already matches.

The playbook is a YAML file. A firm swaps in its own positions, severities and usual responses without a code change, and a changed playbook needs a fresh review (recordings are keyed to it).

## What it was run on

| Leases | What they test |
|---|---|
| 4 Manhattan office leases filed with the SEC as exhibits (`leases/edgar.yml`), 2013 to 2023, two partly redacted by the filer | Long, real leases with defined terms, riders and cross-references. No answer key: the demo page shows the review for a person to judge. |
| 6 constructed leases (`scripts/make_constructed.py`) | Each clause was written to match the standard position, depart from it, or be left out, so the answer key is exact. The recorded run must get 84 of 90 positions right with no critical miss (a departure from a critical position marked consistent); `tests/test_recorded.py` checks this in CI. |

## Run it

```
pip install -e ".[dev]"
pytest -q                                              # no network, no key
python scripts/run_all.py                              # replays the recorded reviews, writes reports/results.json and docs/issues/*.docx
lease-review leases/constructed/constructed-1.txt --out issues.docx
LEASE_LIVE=1 ANTHROPIC_API_KEY=... lease-review my_lease.docx --out issues.docx   # a live review of a new lease (.txt, .html or .docx)
python scripts/build_demo.py                           # rebuilds docs/index.html from reports/results.json
```

## How the live run is recorded

A live run writes every Claude reply to `recordings/reviews.jsonl` with cost and latency, keyed to the lease text, the playbook and the model, effort and prompt version. CI and the demo page replay that recording through the current guardrails, so they need no key and give the same result every time. The **Record a live run** workflow (Actions tab, needs the `ANTHROPIC_API_KEY` secret) downloads the EDGAR leases, records fresh reviews and rebuilds the page.

## CI

Every push runs ruff and the tests on Python 3.10 and 3.12; once a run is recorded, it also grades the recording on the constructed leases and checks that `reports/results.json` matches a fresh replay.

The sample playbook was written for this demo from terms that commonly appear in New York office leases. It is not any firm's playbook and not legal advice. The constructed leases, their parties, addresses and figures are invented.
