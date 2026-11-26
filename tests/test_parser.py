"""Tests for the incident-list parser."""

from datetime import datetime
from pathlib import Path
import sys
import types

package = types.ModuleType("custom_components.kreis_steinfurt")
package.__path__ = [str(Path(__file__).parents[1] / "custom_components" / "kreis_steinfurt")]
sys.modules.setdefault("custom_components.kreis_steinfurt", package)
from custom_components.kreis_steinfurt.parser import parse_einsaetze, parse_pagination


def test_parse_einsaetze() -> None:
    """All fields are read from the public list markup."""
    html = (Path(__file__).parent / "sample_page.html").read_text(encoding="utf-8")

    einsaetze = parse_einsaetze(html)

    assert len(einsaetze) == 2
    assert einsaetze[0].einsatznr == "26058928"
    assert einsaetze[0].einsatzart == "Drehleiter"
    assert einsaetze[0].ort == "Westerkappeln"
    assert einsaetze[0].beginn == datetime(2026, 9, 5, 15, 5)
    assert einsaetze[0].zustand == "laufend"


def test_parse_einsaetze_returns_empty_list_without_rows() -> None:
    """A valid response without entries is not an error."""
    assert parse_einsaetze("<html><body></body></html>") == []


def test_parse_pagination_reads_source_total_and_page_size() -> None:
    """The website's pagination text determines every page to retrieve."""
    html = "<div>Zeige 51 bis 100 von 106</div>"

    assert parse_pagination(html) == (106, 50)


def test_parse_pagination_returns_none_without_page_navigation() -> None:
    """A one-page source does not need pagination requests."""
    assert parse_pagination("<div>Keine weiteren Seiten</div>") is None


def test_parse_einsaetze_ohne_ort_faellt_nicht_aus() -> None:
    """Ein Einsatz ohne (oder mit leerem) Ort legt nicht die ganze Liste lahm."""
    html = """
    <ul>
      <li class="kreisleitsystem-rows">
        <span class="type">RD 1</span>
        <span class="beginn"><span class="beginn-label">Beginn:</span>2026-11-24 11:05:00</span>
        <span class="status"><span class="status-label">Zustand:</span>laufend</span>
        <span class="operation"><span class="operation-label">Einsatznr.:</span>26070001</span>
      </li>
      <li class="kreisleitsystem-rows">
        <span class="type">TH klein</span>
        <span class="city"><span class="city-label">Ort:</span></span>
        <span class="beginn"><span class="beginn-label">Beginn:</span>2026-11-24 11:06:00</span>
        <span class="status"><span class="status-label">Zustand:</span>laufend</span>
        <span class="operation"><span class="operation-label">Einsatznr.:</span>26070002</span>
      </li>
      <li class="kreisleitsystem-rows">
        <span class="type">Brand 1</span>
        <span class="city"><span class="city-label">Ort:</span>Steinfurt</span>
        <span class="beginn"><span class="beginn-label">Beginn:</span>2026-11-24 11:07:00</span>
        <span class="status"><span class="status-label">Zustand:</span>laufend</span>
        <span class="operation"><span class="operation-label">Einsatznr.:</span>26070003</span>
      </li>
    </ul>
    """

    einsaetze = parse_einsaetze(html)

    assert [e.ort for e in einsaetze] == ["Unbekannt", "Unbekannt", "Steinfurt"]
    assert einsaetze[0].einsatzart == "RD 1"
    assert einsaetze[0].einsatznr == "26070001"


def test_parse_einsaetze_ohne_art_und_zustand_faellt_nicht_aus() -> None:
    """Fehlen Einsatzart oder Zustand, steht dort „Unbekannt“."""
    html = """
    <ul>
      <li class="kreisleitsystem-rows">
        <span class="city"><span class="city-label">Ort:</span>Rheine</span>
        <span class="beginn"><span class="beginn-label">Beginn:</span>2026-11-24 11:05:00</span>
        <span class="operation"><span class="operation-label">Einsatznr.:</span>26070010</span>
      </li>
    </ul>
    """

    einsatz = parse_einsaetze(html)[0]

    assert einsatz.einsatzart == "Unbekannt"
    assert einsatz.zustand == "Unbekannt"
    assert einsatz.ort == "Rheine"


def test_parse_einsaetze_ohne_einsatznummer_bleibt_fehler() -> None:
    """Ohne Einsatznummer lassen sich Einsätze nicht unterscheiden: weiter ein Fehler."""
    import pytest

    html = """
    <ul><li class="kreisleitsystem-rows">
      <span class="type">RD 1</span>
      <span class="beginn"><span class="beginn-label">Beginn:</span>2026-11-24 11:05:00</span>
    </li></ul>
    """

    with pytest.raises(ValueError):
        parse_einsaetze(html)
