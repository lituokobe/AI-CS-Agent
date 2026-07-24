"""Shared fixtures for unit tests.

Keep fixtures minimal and self-contained so tests do not depend on Redis,
Milvus, LLM APIs, or full simulated datasets.
"""

from __future__ import annotations

import pytest


@pytest.fixture
def sample_intentions() -> list[dict]:
    return [
        {
            "intention_id": "I001",
            "intention_name": "同意",
            "keywords": ["好的", "可以", "感兴趣"],
            "llm_description": ["用户表示同意或有兴趣"],
        },
        {
            "intention_id": "I002",
            "intention_name": "拒绝",
            "keywords": ["不需要", "没兴趣", "^不想.*了$"],
            "llm_description": ["用户明确拒绝"],
        },
    ]


@pytest.fixture
def sample_knowledge_intentions() -> list[dict]:
    return [
        {
            "intention_id": "K001",
            "intention_name": "问地址",
            "keywords": ["地址", "在哪里"],
            "llm_description": ["询问活动地点"],
            "knowledge_type": 1,
            "answer_type": 1,
            "answer": "上海市浦东新区",
            "other_config": {"match_num": 3},
        },
        {
            "intention_id": "K002",
            "intention_name": "问时间",
            "keywords": ["几点", "什么时候"],
            "llm_description": ["询问活动时间"],
            "knowledge_type": 1,
            "answer_type": 1,
            "answer": "本周六",
            "other_config": {"match_num": 2},
        },
    ]


@pytest.fixture
def minimal_agent_data() -> dict:
    return {
        "enable_nlp": 1,
        "nlp_threshold": 0.8,
        "intention_priority": 3,
        "use_llm": 0,
        "llm_name": "qwen3.5-flash",
        "llm_threshold": 3,
        "llm_context_rounds": 2,
        "llm_role_description": "测试客服",
        "llm_background_info": "测试背景",
        "vector_db_url": "http://127.0.0.1:19530",
        "collection_name": "unit_test_collection",
    }


@pytest.fixture
def minimal_chatflow_design() -> list[dict]:
    return [
        {
            "sort": 1,
            "main_flow_id": "MF1",
            "main_flow_name": "开场",
            "main_flow_content": {
                "starting_node_id": "BN1",
                "base_nodes": [
                    {
                        "node_id": "BN1",
                        "node_name": "开场白",
                        "reply_content_info": [],
                        "intention_branches": [],
                        "other_config": {},
                    },
                    {
                        "node_id": "BN2",
                        "node_name": "确认",
                        "reply_content_info": [],
                        "intention_branches": [],
                        "other_config": {},
                    },
                ],
            },
        },
        {
            "sort": 2,
            "main_flow_id": "MF2",
            "main_flow_name": "邀约",
            "main_flow_content": {
                "starting_node_id": "BN3",
                "base_nodes": [
                    {
                        "node_id": "BN3",
                        "node_name": "邀约确认",
                        "reply_content_info": [],
                        "intention_branches": [],
                        "other_config": {},
                    },
                ],
            },
        },
    ]


@pytest.fixture
def minimal_knowledge(sample_knowledge_intentions) -> list[dict]:
    return sample_knowledge_intentions


@pytest.fixture
def minimal_knowledge_main_flow() -> list[dict]:
    return [
        {
            "main_flow_id": "KMF1",
            "main_flow_name": "地址说明",
            "main_flow_content": {
                "starting_node_id": "KBN1",
                "base_nodes": [
                    {
                        "node_id": "KBN1",
                        "node_name": "地址回复",
                        "reply_content_info": [],
                        "intention_branches": [],
                        "other_config": {},
                    }
                ],
            },
        }
    ]


@pytest.fixture
def minimal_global_configs() -> list[dict]:
    return [
        {
            "status": 1,
            "context_type": 1,
            "reply_content_info": [{"content": "您好还在吗？"}],
        },
        {
            "status": 1,
            "context_type": 2,
            "reply_content_info": [{"content": "抱歉没听清"}],
        },
        {
            "status": 0,
            "context_type": 1,
            "reply_content_info": [{"content": "未启用"}],
        },
    ]
