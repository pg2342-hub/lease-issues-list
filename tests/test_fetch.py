from leasereview.fetch import html_to_text, leases


def test_html_to_text_keeps_paragraphs_and_inline_words():
    html = (
        "<html><style>p{}</style><body><p>ARTICLE 1</p><p>1.1&nbsp;Tenant  sh<span>all</span><br>pay.</p>"
        "<div><font>Landlord</font> <b>may</b> draw.</div><script>x()</script></body></html>"
    )
    text = html_to_text(html)
    assert text.splitlines() == ["ARTICLE 1", "1.1 Tenant shall", "pay.", "Landlord may draw."]
    assert "x()" not in text and "p{}" not in text


def test_edgar_list_points_at_sec_archives():
    rows = leases()
    assert len(rows) == 4
    assert all(r["url"].startswith("https://www.sec.gov/Archives/edgar/data/") for r in rows)
    assert len({r["id"] for r in rows}) == 4
