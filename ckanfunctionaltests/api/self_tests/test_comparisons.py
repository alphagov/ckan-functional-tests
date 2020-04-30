import re
from unittest.mock import ANY

import pytest

from ckanfunctionaltests.api.comparisons import (
    RestrictedAny,
    AnySupersetOf,
    AnyStringMatching,
    ExactIdentity,
)


class TestRestrictedAny:
    def test_any_odd(self):
        any_odd = RestrictedAny(lambda x: x % 2)
        assert (4, 5, 6,) == (4, any_odd, 6,)
        assert (4, 9, 6,) == (4, any_odd, 6,)
        assert not (4, 9, 6,) == (4, any_odd, any_odd,)


class TestAnySupersetOf:
    def test_dict(self):
        assert [{"a": 123, "b": 456, "less": "predictabananas"}, 789] == [AnySupersetOf({"a": 123, "b": 456}), 789]

    def test_dict_identical(self):
        value = {"a": 123, "b": 456, "less": "predictabananas"}
        assert [value, 789] == [AnySupersetOf(value), 789]

    def test_seq(self):
        assert [
            None,
            {"a": 123, "b": 456},
            "foo",
            789,
            "bar",
            "baz",
        ] == AnySupersetOf([
            {"a": 123, "b": 456},
            789,
            "baz",
        ])

    def test_seq_identical(self):
        value = [
            None,
            {"a": 123, "b": 456},
            "foo",
            789,
            "bar",
            "baz",
        ]
        assert value == AnySupersetOf(value)

    def test_seq_wrong_order(self):
        assert [
            None,
            {"a": 123, "b": 456},
            "foo",
            789,
            "bar",
            "baz",
        ] != AnySupersetOf([
            {"a": 123, "b": 456},
            "baz",
            789,
        ])

    def test_seq_any(self):
        assert [
            None,
            {"a": 123, "b": 456},
            "foo",
            789,
            "bar",
            "baz",
        ] == AnySupersetOf([
            {"a": 123, "b": ANY},
            789,
            ANY,
            "baz",
        ])

    def test_seq_any_unmatched(self):
        assert [
            None,
            {"a": 123, "b": 456},
            "foo",
            789,
            "bar",
            "baz",
        ] != AnySupersetOf([
            {"a": 123, "b": ANY},
            789,
            "baz",
            ANY,
        ])

    @pytest.mark.parametrize("recursive", (False, True,))
    @pytest.mark.parametrize("seq_norm_order", (False, True,))
    def test_recursive_alldicts(self, recursive, seq_norm_order):
        # this should be equal only if the recursive flag is True
        assert ({
            "a": 123,
            "b": {
                "c": "foo",
                321: {
                    "x": 456,
                    "y": "bar",
                },
                "d": "baz",
            },
            "less": "predictabananas",
        } == AnySupersetOf({
            "a": 123,
            "b": {
                "c": "foo",
                321: {
                    "y": "bar",
                },
            },
        }, recursive=recursive, seq_norm_order=seq_norm_order)) == recursive

    @pytest.mark.parametrize("recursive", (False, True,))
    @pytest.mark.parametrize("seq_norm_order", (False, True,))
    def test_recursive_alldicts_identical(self, recursive, seq_norm_order):
        value = {
            "a": 123,
            "b": {
                "c": "foo",
                321: {
                    "x": 456,
                    "y": "bar",
                },
                "d": "baz",
            },
            "less": "predictabananas",
        }
        assert value == AnySupersetOf(value, recursive=recursive, seq_norm_order=seq_norm_order)

    @pytest.mark.parametrize("recursive", (False, True,))
    @pytest.mark.parametrize("seq_norm_order", (False, True,))
    def test_recursive_allseqs(self, recursive, seq_norm_order):
        # this should be equal only if the recursive flag is True
        assert ([
            ["a", [2], ["b"], "c", ["d"]],
            123,
            [None, None, ["foo", 321, ["bar"]], None],
            6.7,
        ] == AnySupersetOf([
            [[], "c"],
            123,
            [["foo", ["bar"]], None],
        ], recursive=recursive, seq_norm_order=seq_norm_order)) == recursive

    @pytest.mark.parametrize("recursive", (False, True,))
    @pytest.mark.parametrize("seq_norm_order", (False, True,))
    def test_recursive_allseqs_identical(self, recursive, seq_norm_order):
        value = [
            ["a", [2], ["b"], "c", ["d"]],
            123,
            [None, None, ["foo", 321, ["bar"]], None],
            6.7,
        ]
        assert value == AnySupersetOf(value, recursive=recursive, seq_norm_order=seq_norm_order)

    @pytest.mark.parametrize("recursive", (False, True,))
    @pytest.mark.parametrize("seq_norm_order", (False, True,))
    def test_recursive_mix(self, recursive, seq_norm_order):
        # this should be equal only if the recursive flag is True
        assert ({
            "a": 123,
            "b": [
                {"c": "foo"},
                {
                    321: {
                        "x": 456,
                        "y": ["b", "a", "r"],
                        "z": None,
                        (444, "555"): [],
                    },
                    "654": [1],
                },
                "d",
                "baz",
            ],
            "less": "predictabananas",
        } == AnySupersetOf({
            "a": 123,
            "b": [
                {
                    321: {
                        "y": [ANY],
                        "x": 456,
                    },
                },
                "baz",
            ],
        }, recursive=recursive)) == recursive

    @pytest.mark.parametrize("recursive", (False, True,))
    @pytest.mark.parametrize("seq_norm_order", (False, True,))
    def test_recursive_mix_identical(self, recursive, seq_norm_order):
        value = {
            "a": 123,
            "b": [
                {"c": "foo"},
                {
                    321: {
                        "x": 456,
                        "y": ["b", "a", "r"],
                        "z": None,
                        (444, "555"): [],
                    },
                    "654": [1],
                },
                "d",
                "baz",
            ],
            "less": "predictabananas",
        }
        assert value == AnySupersetOf(value, recursive=recursive, seq_norm_order=seq_norm_order)

    @pytest.mark.parametrize("recursive", (False, True,))
    @pytest.mark.parametrize("seq_norm_order", (False, True,))
    def test_recursive_norm_order(self, recursive, seq_norm_order):
        # this should be equal only if the recursive and seq_norm_order flags are both True
        assert ({
            "a": 123,
            "b": [
                {
                    321: {
                        "x": 456,
                        "y": ["a", "b", "r", "d", "b"],
                        "z": None,
                        (444, "555"): [],
                    },
                    "key": "abc",
                    "654": [1],
                },
                {"c": "foo"},
                {
                    "m": "oof",
                    "name": "moo",
                },
                "e",
                "d",
                "baz",
            ],
            "less": "predictabananas",
        } == AnySupersetOf({
            "a": 123,
            "b": [
                "baz",
                {
                    321: {
                        "y": ["r", "b"],
                        "x": 456,
                    },
                    "key": "abc",
                },
                "d",
            ],
        }, recursive=recursive, seq_norm_order=seq_norm_order)) == (recursive and seq_norm_order)

    @pytest.mark.parametrize("recursive", (False, True,))
    @pytest.mark.parametrize("seq_norm_order", (False, True,))
    def test_recursive_norm_order_not_equal(self, recursive, seq_norm_order):
        assert {
            "a": 123,
            "b": [
                {
                    321: {
                        "x": 456,
                        "y": ["a", "b", "r", "b"],
                        "z": None,
                        (444, "555"): [],
                    },
                    "key": "abc",
                    "654": [1],
                },
                {"c": "foo"},
                {
                    "m": "oof",
                    "name": "moo",
                },
                "e",  # missing "d"
                "baz",
            ],
            "less": "predictabananas",
        } != AnySupersetOf({
            "a": 123,
            "b": [
                "baz",
                {
                    321: {
                        "y": ["b", "r"],
                        "x": 456,
                    },
                    "key": "abc",
                },
                "d",
            ],
        }, recursive=recursive, seq_norm_order=seq_norm_order)


class TestStringMatching:
    def test_string_matching(self):
        assert {"a": "Metempsychosis", "b": "c"} == {"a": AnyStringMatching(r"m+.+psycho.*", flags=re.I), "b": "c"}

    def test_pattern_caching(self):
        # not actually testing that it *is* definitely caching, just checking that it's not broken due to attempted
        # caching
        pattern_a = AnyStringMatching(r"transmigration", flags=re.I)
        pattern_b = AnyStringMatching(r"transmigration")
        pattern_c = AnyStringMatching(r"transmigration", flags=re.I)
        pattern_d = AnyStringMatching(r"Transmigration", flags=re.I)
        pattern_e = AnyStringMatching(r"Transmigration")
        pattern_f = AnyStringMatching(r"transmigration")

        assert {
            "u": "transMigration",
            "v": "transmigration",
            "w": "Transmigration",
            "x": "transmigratioN",
            "y": "Transmigration",
            "z": "transmigration",
        } == {
            "u": pattern_a,
            "v": pattern_b,
            "w": pattern_c,
            "x": pattern_d,
            "y": pattern_e,
            "z": pattern_f,
        }

        assert {
            "u": "transMigration",
            "v": "transmigration",
            "w": "Transmigration",
            "x": "transmigratioN",
            "y": "Transmigration",
            "z": "Transmigration",  # <-- only difference here
        } != {
            "u": pattern_a,
            "v": pattern_b,
            "w": pattern_c,
            "x": pattern_d,
            "y": pattern_e,
            "z": pattern_f,
        }


class TestExactIdentity:
    def test_exact_identity(self):
        x = []
        assert (7, ExactIdentity(x),) == (7, x,)
        assert not (7, ExactIdentity(x),) == (7, [],)
