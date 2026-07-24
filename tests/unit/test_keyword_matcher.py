"""Unit tests for KeywordMatcher (Aho-Corasick + regex)."""

from __future__ import annotations

from functionals.matchers import KeywordMatcher


def test_literal_keyword_hit_and_primary(sample_intentions):
    matcher = KeywordMatcher(sample_intentions)
    result = matcher.analyze_sentence("我很感兴趣，可以了解一下")

    assert "I001" in result
    assert result["I001"]["count"] >= 1
    assert "感兴趣" in result["I001"]["keywords"] or "可以" in result["I001"]["keywords"]

    primary_id, name, keywords, count = KeywordMatcher.get_primary_type(result)
    assert primary_id == "I001"
    assert name == "同意"
    assert count == result["I001"]["count"]
    assert isinstance(keywords, list)


def test_regex_keyword_hit(sample_intentions):
    matcher = KeywordMatcher(sample_intentions)
    result = matcher.analyze_sentence("不想参加了")

    assert "I002" in result
    assert result["I002"]["count"] >= 1
    assert any("^不想.*了$" in k for k in result["I002"]["keywords"])


def test_invalid_regex_is_skipped():
    intentions = [
        {
            "intention_id": "I900",
            "intention_name": "坏正则",
            "keywords": ["[未闭合", "正常词"],
        }
    ]
    matcher = KeywordMatcher(intentions)
    result = matcher.analyze_sentence("这里有正常词")

    assert "I900" in result
    assert "正常词" in result["I900"]["keywords"]


def test_empty_and_blank_keywords_are_ignored():
    matcher = KeywordMatcher(
        [{"intention_id": "I901", "intention_name": "空关键词", "keywords": ["", "  "]}]
    )
    assert matcher.automaton is None
    assert matcher.analyze_sentence("任意输入") == {}


def test_no_intentions():
    matcher = KeywordMatcher([])
    assert matcher.analyze_sentence("你好") == {}


def test_get_primary_type_empty_result():
    primary_id, name, keywords, count = KeywordMatcher.get_primary_type({})
    assert primary_id == "others"
    assert name == ""
    assert keywords == []
    assert count == 0


def test_primary_type_picks_highest_count():
    result = {
        "I001": {"keyword_type": "同意", "count": 1, "keywords": ["好的"]},
        "I002": {"keyword_type": "拒绝", "count": 3, "keywords": ["不需要"] * 3},
    }
    primary_id, name, _, count = KeywordMatcher.get_primary_type(result)
    assert primary_id == "I002"
    assert name == "拒绝"
    assert count == 3


def test_is_probably_regex_heuristic():
    assert KeywordMatcher._is_probably_regex("^abc$") is True
    assert KeywordMatcher._is_probably_regex("普通关键词") is False
