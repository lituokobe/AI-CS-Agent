"""Unit tests for LLMInferenceMatcher JSON output parsing (no LLM I/O)."""

from __future__ import annotations

from functionals.matchers import LLMInferenceMatcher


def test_parse_plain_dict_string():
    text = "{'input_summary': '用户同意参展', 'intention_id': 'I001'}"
    summary, intention_id = LLMInferenceMatcher._parse_llm_json_output(text)
    assert intention_id == "I001"
    assert summary == "用户同意参展"[:10]


def test_parse_fenced_json_block():
    text = """```json
{"input_summary": "询问地址", "intention_id": "K001"}
```"""
    summary, intention_id = LLMInferenceMatcher._parse_llm_json_output(text)
    assert intention_id == "K001"
    assert "询问" in summary or summary == "询问地址"[:10]


def test_parse_malformed_falls_back_to_regex():
    # Fallback regex expects quoted keys when literal_eval fails
    text = 'xxx "input_summary": "摘要内容", "intention_id": "I002" yyy'
    summary, intention_id = LLMInferenceMatcher._parse_llm_json_output(text)
    assert intention_id == "I002"
    assert summary == "摘要内容"[:10]


def test_parse_completely_invalid_defaults():
    summary, intention_id = LLMInferenceMatcher._parse_llm_json_output("not json at all")
    assert summary == "无"
    assert intention_id == "others"
