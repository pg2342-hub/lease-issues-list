"""Download public lease exhibits from SEC EDGAR and turn them into plain text.

EDGAR asks automated clients to identify themselves in the User-Agent and to stay under ten
requests a second; this fetches a handful of files, one at a time.
"""

from __future__ import annotations

import re
import time
from pathlib import Path

import requests
import yaml
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
LIST = ROOT / "leases" / "edgar.yml"
OUT = ROOT / "leases" / "edgar"
BLOCKS = ["p", "div", "tr", "li", "h1", "h2", "h3", "h4", "h5", "h6", "table", "center"]
USER_AGENT = "lease-issues-list 273664482+pg2342-hub@users.noreply.github.com"
HEADERS = {"User-Agent": USER_AGENT, "Accept-Encoding": "gzip, deflate", "Host": "www.sec.gov"}


def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    for br in soup.find_all("br"):
        br.replace_with("\n")
    # Block elements end a line; inline elements (spans, fonts) do not, so words split across
    # styled runs stay whole and a quote can match them.
    for tag in soup.find_all(BLOCKS):
        tag.append("\n")
    text = soup.get_text("")
    lines = [re.sub(r"[ \t ]+", " ", line).strip() for line in text.splitlines()]
    out: list[str] = []
    for line in lines:
        if line or (out and out[-1]):
            out.append(line)
    return "\n".join(out).strip() + "\n"


def leases() -> list[dict]:
    return yaml.safe_load(LIST.read_text())["leases"]


def fetch_all(force: bool = False) -> list[Path]:
    OUT.mkdir(parents=True, exist_ok=True)
    paths = []
    for lease in leases():
        path = OUT / f"{lease['id']}.txt"
        if force or not path.exists():
            r = requests.get(lease["url"], headers=HEADERS, timeout=60)
            r.raise_for_status()
            path.write_text(html_to_text(r.text), encoding="utf-8")
            time.sleep(0.5)
        paths.append(path)
    return paths


if __name__ == "__main__":
    for p in fetch_all():
        print(p.relative_to(ROOT), p.stat().st_size, "bytes")
