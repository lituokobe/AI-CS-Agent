"""Unit tests for dialog stack reducer."""

from __future__ import annotations

from functionals.state import update_dialog_stack


def test_none_keeps_stack():
    assert update_dialog_stack(["a", "b"], None) == ["a", "b"]


def test_pop_removes_last():
    assert update_dialog_stack(["a", "b", "c"], "pop") == ["a", "b"]


def test_pop_empty_stack():
    assert update_dialog_stack([], "pop") == []


def test_append_string():
    assert update_dialog_stack(["a"], "b") == ["a", "b"]


def test_extend_list():
    assert update_dialog_stack(["a"], ["b", "c"]) == ["a", "b", "c"]


def test_unsupported_type_fallback():
    assert update_dialog_stack(["a"], 123) == ["a"]  # type: ignore[arg-type]
