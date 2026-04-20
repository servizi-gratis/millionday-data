from cloud_source import parse_archive_html


def test_parse_archive_html_modern_and_legacy_rows() -> None:
    html = """
    <html><body>
    <h1>Archivio Estrazioni Million Day</h1>
    <p>Data Numeri estratti Numeri EXTRA</p>
    <p>Domenica 19 Aprile 2026 ore 20:30 6 36 41 47 54 19 21 28 30 35</p>
    <p>Domenica 19 Aprile 2026 ore 13:00 4 26 32 40 43 3 29 37 42 50</p>
    <p>Mercoledì 7 Febbraio 2018 ore 20:30 16 7 43 44 51</p>
    <p>Back to top</p>
    </body></html>
    """
    draws = parse_archive_html(html)
    assert len(draws) == 3
    assert draws[0]["draw_id"] == "2018-02-07-evening"
    assert draws[-1]["draw_id"] == "2026-04-19-evening"
    assert draws[-1]["extra_numbers"] == [19, 21, 28, 30, 35]
    assert draws[0]["extra_numbers"] == []
