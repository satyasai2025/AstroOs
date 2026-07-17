from datetime import date

from apps.api.services.dasha_lookup import find_active_dasha_chain


class TestFindActiveDashaChain:
    def test_finds_first_mahadasha_and_its_antardasha(self, simple_dasha_tree):
        chain = find_active_dasha_chain(simple_dasha_tree, date(2001, 6, 1))
        assert [p.lord for p in chain] == ["jupiter", "ketu"]
        assert [p.level for p in chain] == [1, 2]

    def test_finds_second_antardasha_within_same_mahadasha(self, simple_dasha_tree):
        chain = find_active_dasha_chain(simple_dasha_tree, date(2005, 1, 1))
        assert [p.lord for p in chain] == ["jupiter", "venus"]

    def test_finds_second_mahadasha_with_no_sub_periods(self, simple_dasha_tree):
        chain = find_active_dasha_chain(simple_dasha_tree, date(2015, 1, 1))
        assert [p.lord for p in chain] == ["saturn"]

    def test_start_boundary_is_inclusive(self, simple_dasha_tree):
        chain = find_active_dasha_chain(simple_dasha_tree, date(2000, 1, 1))
        assert chain[0].lord == "jupiter"

    def test_end_boundary_is_exclusive_and_falls_into_next_period(self, simple_dasha_tree):
        # 2010-01-01 is jupiter's end AND saturn's start — must resolve to saturn.
        chain = find_active_dasha_chain(simple_dasha_tree, date(2010, 1, 1))
        assert chain[0].lord == "saturn"

    def test_date_before_tree_start_returns_empty_chain(self, simple_dasha_tree):
        chain = find_active_dasha_chain(simple_dasha_tree, date(1999, 1, 1))
        assert chain == ()

    def test_date_on_or_after_final_end_returns_empty_chain(self, simple_dasha_tree):
        chain = find_active_dasha_chain(simple_dasha_tree, date(2029, 1, 1))
        assert chain == ()

    def test_does_not_mutate_or_recompute_the_tree(self, simple_dasha_tree):
        before = simple_dasha_tree.mahadashas
        find_active_dasha_chain(simple_dasha_tree, date(2001, 6, 1))
        assert simple_dasha_tree.mahadashas is before
