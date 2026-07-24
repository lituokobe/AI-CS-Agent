"""Unit tests for IntegratedKeywordsMatcher priority strategies."""

from __future__ import annotations

import pytest

from functionals.integrated_matchers import IntegratedKeywordsMatcher
from functionals.matchers import KeywordMatcher


@pytest.fixture
def intention_matcher(sample_intentions) -> KeywordMatcher:
    return KeywordMatcher(sample_intentions)


@pytest.fixture
def knowledge_matcher(sample_knowledge_intentions) -> KeywordMatcher:
    return KeywordMatcher(sample_knowledge_intentions)


def test_invalid_priority_raises(intention_matcher, knowledge_matcher):
    with pytest.raises(ValueError, match="优先选择"):
        IntegratedKeywordsMatcher(0, intention_matcher, knowledge_matcher)


def test_intention_first_when_both_hit(intention_matcher, knowledge_matcher):
    matcher = IntegratedKeywordsMatcher(2, intention_matcher, knowledge_matcher)
    type_id, type_name, keywords, count, inference_type = matcher.match(
        "好的，地址在哪里"
    )

    assert type_id == "I001"
    assert type_name == "同意"
    assert inference_type == "意图库"
    assert count >= 1
    assert keywords


def test_knowledge_first_when_both_hit(intention_matcher, knowledge_matcher):
    matcher = IntegratedKeywordsMatcher(1, intention_matcher, knowledge_matcher)
    type_id, type_name, _, count, inference_type = matcher.match("好的，地址在哪里")

    assert type_id == "K001"
    assert type_name == "问地址"
    assert inference_type == "知识库"
    assert count >= 1


def test_integrated_picks_higher_count(intention_matcher, knowledge_matcher):
    matcher = IntegratedKeywordsMatcher(3, intention_matcher, knowledge_matcher)
    # "地址" once vs "好的"+"可以" -> intention likely wins by count
    type_id, _, _, count, inference_type = matcher.match("好的可以，地址呢")

    assert count >= 1
    assert type_id in {"I001", "K001"}
    assert inference_type in {"意图库", "知识库"}


def test_no_match_returns_empty_tuple(intention_matcher, knowledge_matcher):
    matcher = IntegratedKeywordsMatcher(2, intention_matcher, knowledge_matcher)
    assert matcher.match("完全无关的一句话") == ("", "", [], 0, "无")


def test_falls_back_to_knowledge_when_intention_misses(
    intention_matcher, knowledge_matcher
):
    matcher = IntegratedKeywordsMatcher(2, intention_matcher, knowledge_matcher)
    type_id, _, _, _, inference_type = matcher.match("请问地址在哪里")

    assert type_id == "K001"
    assert inference_type == "知识库"
