from official_source import parse_archive_payload


def test_parse_archive_payload_skips_pending_and_handles_legacy_rows() -> None:
    payload = [
        {
            "progressivo": 20260512,
            "data": 1778610600000,
            "numeriEstratti": [],
            "numeriEstrattiOvertime": [],
            "progressivoGiornaliero": 2,
            "orarioEstrazione": "20:30",
            "numeroMilionari": None,
        },
        {
            "progressivo": 20260512,
            "data": 1778583600000,
            "numeriEstratti": ["9", "14", "22", "35", "41"],
            "numeriEstrattiOvertime": ["16", "18", "38", "39", "42"],
            "progressivoGiornaliero": 1,
            "orarioEstrazione": "13:00",
            "numeroMilionari": 0,
        },
        {
            "progressivo": 20180207,
            "data": 1517958000000,
            "numeriEstratti": ["7", "16", "43", "44", "51"],
            "numeriEstrattiOvertime": [],
            "progressivoGiornaliero": 2,
            "orarioEstrazione": "20:30",
            "numeroMilionari": None,
        },
    ]

    draws = parse_archive_payload(payload)

    assert len(draws) == 2
    assert draws[0]["draw_id"] == "2018-02-07-evening"
    assert draws[0]["extra_numbers"] == []
    assert draws[1]["draw_id"] == "2026-05-12-midday"
    assert draws[1]["extra_numbers"] == [16, 18, 38, 39, 42]
    assert draws[1]["source"] == "lotto-italia.it"
