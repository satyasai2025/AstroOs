"""
AstroOS - Unit Tests for TerminologyService
"""

import pytest

from apps.api.services.terminology_service import TerminologyService


def test_graha_bidirectional_resolution():
    """Resolves Sanskrit, IAST, and Hindi/Devanagari names to canonical English keys."""
    assert TerminologyService.resolve_graha("guru") == "jupiter"
    assert TerminologyService.resolve_graha("brihaspati") == "jupiter"
    assert TerminologyService.resolve_graha("बृहस्पति") == "jupiter"
    assert TerminologyService.resolve_graha("surya") == "sun"
    assert TerminologyService.resolve_graha("aditya") == "sun"
    assert TerminologyService.resolve_graha("kuja") == "mars"
    assert TerminologyService.resolve_graha("mangal") == "mars"
    assert TerminologyService.resolve_graha("shani") == "saturn"
    assert TerminologyService.resolve_graha("shukra") == "venus"
    assert TerminologyService.resolve_graha("budha") == "mercury"
    assert TerminologyService.resolve_graha("chandra") == "moon"
    assert TerminologyService.resolve_graha("rahu") == "rahu"
    assert TerminologyService.resolve_graha("ketu") == "ketu"


def test_rashi_bidirectional_resolution():
    """Resolves Sanskrit and Devanagari sign names to canonical English keys."""
    assert TerminologyService.resolve_rashi("mesha") == "aries"
    assert TerminologyService.resolve_rashi("मेष") == "aries"
    assert TerminologyService.resolve_rashi("vrishabha") == "taurus"
    assert TerminologyService.resolve_rashi("karka") == "cancer"
    assert TerminologyService.resolve_rashi("simha") == "leo"
    assert TerminologyService.resolve_rashi("dhanu") == "sagittarius"
    assert TerminologyService.resolve_rashi("makara") == "capricorn"
    assert TerminologyService.resolve_rashi("kumbha") == "aquarius"
    assert TerminologyService.resolve_rashi("meena") == "pisces"


def test_bhava_and_house_group_resolution():
    """Resolves Bhava Sanskrit names and groups like Kendra, Trikona, Dusthana."""
    assert TerminologyService.resolve_bhava("lagna") == 1
    assert TerminologyService.resolve_bhava("dhana") == 2
    assert TerminologyService.resolve_bhava("kalatra") == 7
    assert TerminologyService.resolve_bhava("karma") == 10
    assert TerminologyService.resolve_bhava("vyaya") == 12

    assert TerminologyService.resolve_house_group("kendra") == [1, 4, 7, 10]
    assert TerminologyService.resolve_house_group("trikona") == [1, 5, 9]
    assert TerminologyService.resolve_house_group("dusthana") == [6, 8, 12]
    assert TerminologyService.resolve_house_group("upachaya") == [3, 6, 10, 11]


def test_query_expansion_for_retrieval():
    """Query expansion enriches Sanskrit terms with English canonicals and synonyms."""
    expanded = TerminologyService.expand_query_tokens("Guru in Kendra yoga")
    assert "jupiter" in expanded
    assert "guru" in expanded
    assert "brihaspati" in expanded
    assert "1" in expanded
    assert "4" in expanded
    assert "7" in expanded
    assert "10" in expanded
