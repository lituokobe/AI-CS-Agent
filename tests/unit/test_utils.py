"""Unit tests for functionals.utils pure helpers."""

from __future__ import annotations

import pytest

from functionals import utils


class TestMessageHelpers:
    def test_get_last_user_message(self):
        human = type("HumanMessage", (), {"content": "你好"})()
        ai = type("AIMessage", (), {"content": "您好"})()
        assert utils.get_last_user_message([ai, human, ai]) == "你好"
        assert utils.get_last_user_message([ai]) == ""

    def test_last_message_is_ai(self):
        human = type("HumanMessage", (), {"content": "你好"})()
        ai = type("AIMessage", (), {"content": "您好"})()
        empty_ai = type("AIMessage", (), {"content": ""})()

        assert utils.last_message_is_ai([human, ai]) is True
        assert utils.last_message_is_ai([ai, human]) is False
        assert utils.last_message_is_ai([empty_ai]) is False
        assert utils.last_message_is_ai([]) is False


class TestFilters:
    def test_str_dict_select_ok(self):
        src = {"001": {"label": ["a"]}, "002": {"label": ["b"]}}
        assert utils.str_dict_select(src, ["001"]) == {"001": {"label": ["a"]}}

    def test_str_dict_select_empty_ids(self):
        assert utils.str_dict_select({"001": {}}, None) == {}
        assert utils.str_dict_select({"001": {}}, []) == {}

    def test_str_dict_select_missing_raises(self):
        with pytest.raises(ValueError, match="不存在"):
            utils.str_dict_select({"001": {}}, ["001", "999"])

    def test_intention_filter_ok(self, sample_intentions):
        filtered = utils.intention_filter(sample_intentions, {"I002"})
        assert len(filtered) == 1
        assert filtered[0]["intention_id"] == "I002"

    def test_intention_filter_empty_ids(self, sample_intentions):
        assert utils.intention_filter(sample_intentions, None) == []
        assert utils.intention_filter(sample_intentions, set()) == []

    def test_intention_filter_missing_raises(self, sample_intentions):
        with pytest.raises(ValueError, match="不存在"):
            utils.intention_filter(sample_intentions, {"I001", "I999"})


class TestProcessReply:
    def test_no_variate(self):
        dialog_id, content, variate, reply = utils.process_reply(
            {"dialog_id": "d1", "content": "您好", "variate": {}},
            "用户话",
        )
        assert dialog_id == "d1"
        assert content == "您好"
        assert reply == "您好"

    def test_dynamic_var_disabled_replaces_with_empty(self):
        content_info = {
            "dialog_id": "d1",
            "content": "欢迎来到${公司}",
            "variate": {
                "${公司}": {
                    "content_type": 2,
                    "dynamic_var_set_type": 0,
                    "value": "巨峰",
                }
            },
        }
        _, _, _, reply = utils.process_reply(content_info, "任意")
        assert reply == "欢迎来到"

    def test_dynamic_var_constant(self):
        content_info = {
            "dialog_id": "d1",
            "content": "欢迎来到${公司}",
            "variate": {
                "${公司}": {
                    "content_type": 2,
                    "dynamic_var_set_type": 1,
                    "value": "巨峰",
                }
            },
        }
        _, _, _, reply = utils.process_reply(content_info, "任意")
        assert reply == "欢迎来到巨峰"

    def test_dynamic_var_capture_user_input(self):
        content_info = {
            "dialog_id": "d1",
            "content": "您说的是${原话}",
            "variate": {
                "${原话}": {
                    "content_type": 2,
                    "dynamic_var_set_type": 2,
                    "value": "",
                }
            },
        }
        _, _, _, reply = utils.process_reply(content_info, "汤臣一品")
        assert reply == "您说的是汤臣一品"

    def test_invalid_dynamic_var_set_type_raises(self):
        content_info = {
            "dialog_id": "d1",
            "content": "x${v}",
            "variate": {
                "${v}": {"content_type": 2, "dynamic_var_set_type": 9, "value": ""}
            },
        }
        with pytest.raises(ValueError, match="dynamic_var_set_type"):
            utils.process_reply(content_info, "x")

    def test_variate_not_dict_raises(self):
        with pytest.raises(TypeError, match="variate应为字典"):
            utils.process_reply(
                {"dialog_id": "d1", "content": "x", "variate": ["bad"]},
                "x",
            )


class TestFlowHelpers:
    def test_update_target_with_and_without_lookup(self):
        assert utils.update_target("MF2", {"MF2": "BN3"}) == "BN3_reply"
        assert utils.update_target("BN1", {}) == "BN1_reply"

    def test_next_main_flow(self):
        sort_lookup = {"MF1": 1, "MF2": 2, "MF3": 3}
        assert utils.next_main_flow("MF1", sort_lookup) == "MF2"
        assert utils.next_main_flow("MF2", sort_lookup) == "MF3"
        assert utils.next_main_flow("MF3", sort_lookup) is None


class TestLogHelpers:
    def test_get_last_user_log_index_and_slice(self):
        logs = [
            {"role": "assistant", "content": "a"},
            {"role": "user", "content": "u1"},
            {"role": "assistant", "content": "b"},
            {"role": "user", "content": "u2"},
            {"role": "assistant", "content": "c"},
        ]
        assert utils.get_last_user_log_index(logs) == 3
        assert utils.get_last_user_log(logs)["content"] == "u2"
        assert utils.get_logs_from_last_user(logs) == logs[3:]

    def test_get_last_user_log_none(self):
        logs = [{"role": "assistant", "content": "a"}]
        assert utils.get_last_user_log_index(logs) is None
        assert utils.get_last_user_log(logs) is None
        assert utils.get_logs_from_last_user(logs) == logs
