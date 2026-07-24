"""Unit tests for ChatFlowConfig.from_files parsing."""

from __future__ import annotations

import pytest

from config.config_setup import ChatFlowConfig


def test_from_files_builds_contexts(
    minimal_agent_data,
    minimal_knowledge,
    minimal_knowledge_main_flow,
    minimal_chatflow_design,
    minimal_global_configs,
    sample_intentions,
):
    config = ChatFlowConfig.from_files(
        minimal_agent_data,
        minimal_knowledge,
        minimal_knowledge_main_flow,
        minimal_chatflow_design,
        minimal_global_configs,
        sample_intentions,
    )

    assert config.agent_config.enable_nlp == 1
    assert config.agent_config.nlp_threshold == 0.8
    assert config.agent_config.collection_name == "unit_test_collection"

    design = config.chatflow_design_context
    assert design.starting_node_id == "BN1"
    assert design.sort_lookup == {"MF1": 1, "MF2": 2}
    assert design.starting_node_lookup["MF1"] == "BN1"
    assert design.starting_node_lookup["KMF1"] == "KBN1"
    assert "BN1" in design.mf_node_ids
    assert "BN3" in design.mf_node_ids
    assert "BN1" in design.mf_starting_node_ids
    assert "KBN1" not in design.mf_starting_node_ids

    knowledge = config.knowledge_context
    assert knowledge.infer_name["K001"] == "问地址"
    assert knowledge.match_lookup["K001"] == 3
    assert "KMF1" in knowledge.main_flow_ids

    global_ctx = config.global_config_context
    assert global_ctx.no_input is True
    assert global_ctx.no_infer_result is True
    # status=0 entry is filtered out
    assert len(global_ctx.global_configs) == 2
    assert config.intentions == sample_intentions


def test_match_num_defaults_when_invalid(
    minimal_agent_data,
    minimal_chatflow_design,
    sample_intentions,
):
    knowledge = [
        {
            "intention_id": "K010",
            "intention_name": "默认次数",
            "llm_description": [],
            "knowledge_type": 1,
            "answer_type": 1,
            "answer": "x",
            "other_config": {"match_num": -1},
        }
    ]
    config = ChatFlowConfig.from_files(
        minimal_agent_data,
        knowledge,
        [],
        minimal_chatflow_design,
        [],
        sample_intentions,
    )
    assert config.knowledge_context.match_lookup["K010"] == 10000


def test_invalid_chatflow_flow_type_raises(
    minimal_agent_data,
    sample_intentions,
):
    with pytest.raises(TypeError, match="主流程数据应为字典"):
        ChatFlowConfig.from_files(
            minimal_agent_data,
            [],
            [],
            ["not-a-dict"],  # type: ignore[list-item]
            [],
            sample_intentions,
        )


def test_empty_starting_node_id_raises(
    minimal_agent_data,
    sample_intentions,
):
    bad_design = [
        {
            "sort": 1,
            "main_flow_id": "MF1",
            "main_flow_name": "坏流程",
            "main_flow_content": {
                "starting_node_id": "",
                "base_nodes": [],
            },
        }
    ]
    with pytest.raises(TypeError, match="初始节点id"):
        ChatFlowConfig.from_files(
            minimal_agent_data,
            [],
            [],
            bad_design,
            [],
            sample_intentions,
        )
