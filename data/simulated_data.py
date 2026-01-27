agent_data = {
    "enable_nlp": 1,
    "nlp_threshold": 0.5,
    "intention_priority": 1,
    "use_llm": 1,
    "llm_name": "deepseek_llm",
    "llm_threshold": 2,
    "llm_context_rounds": 10,
    "llm_role_description": "你是一个专业的家装平台的电话营销专员，你的任务是获取上海可能有装修意向的客户",
    "llm_background_info": "你现在正在沟通的都是可能会有装修需求的人，请尽量引导客户加微信",
    "vector_db_url": "http://127.0.0.1:19530",
    "collection_name": "tel33ccc"
}
intentions = [
    {
        "intention_id": "c9a32efe093c66b0",
        "intention_name": "拒绝",
        "keywords": ["不需要", "别再打 电话了", "没报过名"],
        "semantic": ["没这方面的需要", "不需要，别再打电话了", "没报过名，哪来 的电话"],
        "llm_description": ["没这方面的需要"]
    },
    {
        "intention_id": "3b1dd074153d2164",
        "intention_name": "否定",
        "keywords": ["没需求", "不需要", "不用了", "别再打电话了", "先不用", "不 可以", "不了解", "算了吧", "顾不上", "目前不需要", "不用介绍", "没有意向", "不会搞", "不方便", "暂时不需要", "没需要", "不用智能手机", "别废话", "没这人", "没钱", "没有这个意向", "没有钱", "不打算"],
        "semantic": ["装修完了", "没这方面需求", "不想参加", "没兴趣", "在忙，以后有机 会再说", "对这个不兴趣", "对这个没兴趣", "不用不用", "没兴趣听你说", "先不弄这个", "我们不做 这个", "用不到这些", "这个不要了", "谢谢我不需要", "没这方面的需求", "这个我不用", "别加我", "这个我们不用", "我这个是老年机", "明年再说", "我明年才要装修", "我目前不需要装修", "好的，最近没这个打算", "你好，目前没有计划", "我们没有装修的打算", "不需要装修", "别说了", "不要给我 介绍了"],
        "llm_description": ["近期无装修需求，不需要"]
    },
    {
        "intention_id": "1574528df2dbe465",
        "intention_name": "肯定",
        "keywords": ["好的", "没问题", "什么时间", "地点在哪里", "发吧", "没问题", "我要", "再联系", "嗯可以", "就是这个手机", "嗯寄吧", "行的", "行行行", "太好了", "免费就要", "等会给我打", "好的好的", "到时候打给你", "等会再打", "晚点打", "过一会打", "发我 信息吧", "你加我微信上说把", "微信号就是手机", "好呢", "微信沟通", "资料用微信发给我", "你加 吧", "加我的电话", "可以", "可以", "在哪里"],
        "semantic": ["正好近期要装修", "有时间过去看看", "在什么位置", "有这方面需求的", "有这方面想法", "我家房子需要翻新", "等我有空的时候去看下", "我正好需要装修", "我有时间过去看下", "到时候我去现场看下", "我正好有房子需要装修", "我正好 有房子要装修", "我有房子需要翻新", "我家里正好有个老房子", "那你快递一份资料吧", "你给我邮寄 一份吧", "把资料发给我", "让他加我微信说", "资料发我微信", "你给我寄一份吧"],
        "llm_description": ["近期有装修需求，能参加"]
    }
]
knowledge = []
chatflow_design = [
    {
        "main_flow_id": "4e7b2f4f637d0baa",
        "main_flow_name": "主流程一",
        "main_flow_content": {
            "starting_node_id": "node-1765344497783-3431",
            "base_nodes": [{
                "node_id": "node-1765344497783-3431",
                "node_name": "开场白",
                "reply_content_info": [{
                    "dialog_id": "48592a6f42891500",
                    "content": "喂，您好，{{停顿1秒}} 我是福居家博会的客服，近期我们针对保利业主举办了一个关于老房子翻新，毛坯房设计，和局部改动的实景样板房体验展，如果您近期或者明年有装修计划的话，都可以到现场免费的咨询了解一下。",
                    "variate": []
                }],
                "intention_branches": [{
                    "branch_id": "d2000e2526034f91a57024bd3cd1bbe9",
                    "branch_name": "默认",
                    "branch_type": "DEFAULT",
                    "intention_ids": None
                }, {
                    "branch_id": "eef07034f47148d1976365450cb6e59a",
                    "branch_name": "肯定",
                    "branch_type": "SURE",
                    "intention_ids": ["1574528df2dbe465"]
                }, {
                    "branch_id": "7516e93af81e4db9a4125e6b0e988fd3",
                    "branch_name": "否定",
                    "branch_type": "DENY",
                    "intention_ids": ["3b1dd074153d2164"]
                }],
                "enable_logging": True,
                "other_config": {
                    "is_break": 1,
                    "break_time": "0.0",
                    "interrupt_knowledge_ids": "",
                    "wait_time": "3.5",
                    "intention_tag": "",
                    "no_asr": 0,
                    "nomatch_knowledge_ids": []
                }
            }, {
                "node_id": "node-1765344824009-2896",
                "node_name": "普通节点",
                "reply_content_info": [{
                    "dialog_id": "f17aa3e3d9b7a0c6",
                    "content": "是这样的，近期在国家会议中心有个免费的家装实景体验展，现场您可以了解到智能家居 ，以及不同的装修风格，您看有没有兴趣来体验一下？",
                    "variate": []
                }],
                "intention_branches": [{
                    "branch_id": "87c4ba0c0daf48e795abec365189a24f",
                    "branch_name": "肯定",
                    "branch_type": "SURE",
                    "intention_ids": ["1574528df2dbe465"]
                }, {
                    "branch_id": "8cf51f0d13b440e2b58365caa40b1e7b",
                    "branch_name": "否定",
                    "branch_type": "DENY",
                    "intention_ids": ["3b1dd074153d2164"]
                }],
                "enable_logging": True,
                "other_config": {
                    "is_break": 1,
                    "break_time": "0.0",
                    "interrupt_knowledge_ids": "",
                    "wait_time": "3.5",
                    "intention_tag": "",
                    "no_asr": 0,
                    "nomatch_knowledge_ids": []
                }
            }, {
                "node_id": "node-1765345035862-4426",
                "node_name": "普通节点",
                "reply_content_info": [{
                    "dialog_id": "14cc632f77d3e3da",
                    "content": "咱们现在不考虑也可以先过来了解一下目前装修市场的人工材料的费用，可以避免后期装修的一些猫腻和水分，现场是有最新风格的实景样板房可以免费参观体验，如 果您家里近两年可能有装修的想法都可以先过来参观了解一下的",
                    "variate": []
                }],
                "intention_branches": [{
                    "branch_id": "440e31e5bb53430eb40972f0fd33fbe5",
                    "branch_name": "默认",
                    "branch_type": "DEFAULT",
                    "intention_ids": None
                }, {
                    "branch_id": "9e69ea737bc1404ab6e594a322f67025",
                    "branch_name": "拒绝",
                    "branch_type": "REJECT",
                    "intention_ids": ["c9a32efe093c66b0"]
                }],
                "enable_logging": True,
                "other_config": {
                    "is_break": 1,
                    "break_time": "0.0",
                    "interrupt_knowledge_ids": "",
                    "wait_time": "3.5",
                    "intention_tag": "",
                    "no_asr": 0,
                    "nomatch_knowledge_ids": []
                }
            }],
            "transfer_nodes": [{
                "node_id": "node-1765345149182-9775",
                "node_name": "跳转节点",
                "reply_content_info": [{
                    "dialog_id": "5f2fc673ec171881",
                    "content": "不管您来不来，如果近一年内有装修需求 ，我们都可以免费提供两本针对上海业主的装修宝典给您，一本是总结了近十年内装修业主的心得体会和 装修猫腻，另外一本是目前市面上热门主辅材的品牌型号价格表。稍后让我们家装顾问和您联系确认具体 情况，您看可以吗？",
                    "variate": []
                }],
                "action": 2,
                "master_process_id": "",
                "enable_logging": True,
                "other_config": {
                    "intention_tag": "",
                    "no_asr": 0,
                    "nomatch_knowledge_ids": ""
                }
            }, {
                "node_id": "node-1765345584454-9343",
                "node_name": "跳转节点",
                "reply_content_info": [{
                    "dialog_id": "94135539dd8e3136",
                    "content": "不好意思，打扰您了，再见",
                    "variate": []
                }],
                "action": 1,
                "master_process_id": "",
                "enable_logging": True,
                "other_config": {
                    "intention_tag": "",
                    "no_asr": 0,
                    "nomatch_knowledge_ids": ""
                }
            }],
            "edge_setups": [{
                "node_id": "node-1765344497783-3431",
                "node_name": "开场白",
                "route_map": {
                    "d2000e2526034f91a57024bd3cd1bbe9": "node-1765344824009-2896",
                    "eef07034f47148d1976365450cb6e59a": "node-1765344824009-2896",
                    "7516e93af81e4db9a4125e6b0e988fd3": "node-1765345035862-4426"
                },
                "enable_logging": True
            }, {
                "node_id": "node-1765344824009-2896",
                "node_name": "普通节点",
                "route_map": {
                    "87c4ba0c0daf48e795abec365189a24f": "node-1765345149182-9775"
                },
                "enable_logging": True
            }, {
                "node_id": "node-1765345035862-4426",
                "node_name": "普通节点",
                "route_map": {
                    "440e31e5bb53430eb40972f0fd33fbe5": "node-1765345149182-9775",
                    "9e69ea737bc1404ab6e594a322f67025": "node-1765345584454-9343"
                },
                "enable_logging": True
            }]
    },
    "sort": 0
}, {
    "main_flow_id": "ce9c687c2c2818be",
    "main_flow_name": "主线流程二——介绍开场白",
    "main_flow_content": {
        "starting_node_id": "node-1765345629418-6861",
        "base_nodes": [{
            "node_id": "node-1765345629418-6861",
            "node_name": "主线流程二——介绍开场白",
            "reply_content_info": [{
                "dialog_id": "9fee29659412b97e",
                "content": "是这样的，我们这里于2025.12.25在国家会议中心举 办福居第3届沧州家博会，您有时间参加吗",
                "variate": []
            }],
            "intention_branches": [{
                "branch_id": "9b16f3eded9c4a7e966594b8efefd5f7",
                "branch_name": "默认",
                "branch_type": "DEFAULT",
                "intention_ids": None
            }, {
                "branch_id": "37d073d72185462693bd53cd3b536990",
                "branch_name": "肯定",
                "branch_type": "SURE",
                "intention_ids": ["1574528df2dbe465"]
            }, {
                "branch_id": "b28dde69948744ae8fcce27a7c47c16a",
                "branch_name": "否定",
                "branch_type": "DENY",
                "intention_ids": ["3b1dd074153d2164"]
            }],
            "enable_logging": True,
            "other_config": {
                "is_break": 1,
                "break_time": "0.0",
                "interrupt_knowledge_ids": "",
                "wait_time": "3.5",
                "intention_tag": "",
                "no_asr": 0,
                "nomatch_knowledge_ids": []
            }
        }, {
            "node_id": "node-1765345710608-1633",
            "node_name": "普通节点",
            "reply_content_info": [{
                "dialog_id": "5a93376085181ae7",
                "content": "本次展会现场是有直接还原了在建工地 样板间和本年度最新风格的整体实景样板房，对未来装修非常有借鉴意义，您看是不是来免费体验一下",
                "variate": []
            }],
            "intention_branches": [{
                "branch_id": "8c5bc4f5f61a41209cad51b13b69d44e",
                "branch_name": "默认",
                "branch_type": "DEFAULT",
                "intention_ids": None
            }, {
                "branch_id": "bea0d9f799704d1a8595426e25908399",
                "branch_name": "肯定",
                "branch_type": "SURE",
                "intention_ids": ["1574528df2dbe465"]
            }, {
                "branch_id": "189121c3dead4479b50a9445ee6eb8fa",
                "branch_name": "否定",
                "branch_type": "DENY",
                "intention_ids": ["3b1dd074153d2164"]
            }],
            "enable_logging": True,
            "other_config": {
                "is_break": 1,
                "break_time": "0.0",
                "interrupt_knowledge_ids": "",
                "wait_time": "3.5",
                "intention_tag": "",
                "no_asr": 0,
                "nomatch_knowledge_ids": []
            }
        }],
        "transfer_nodes": [{
            "node_id": "node-1765345824497-9287",
            "node_name": "跳转节点",
            "reply_content_info": [{
                "dialog_id": "1fe9ab401273b6d5",
                "content": "打扰您了，再见",
                "variate": []
            }],
            "action": 1,
            "master_process_id": "",
            "enable_logging": True,
            "other_config": {
                "intention_tag": "",
                "no_asr": 0,
                "nomatch_knowledge_ids": ""
            }
        }, {
            "node_id": "node-1765346585901-6884",
            "node_name": "跳转节点",
            "reply_content_info": [{
                "dialog_id": "8a1d88dda2e55feb",
                "content": "好的，稍后给您发邀请函 及活动介绍，祝您生活愉快，再见",
                "variate": []
            }],
            "action": 1,
            "master_process_id": "",
            "enable_logging": True,
            "other_config": {
                "intention_tag": "",
                "no_asr": 0,
                "nomatch_knowledge_ids": ""
            }
        }, {
            "node_id": "node-1765346610648-5912",
            "node_name": "跳转节点",
            "reply_content_info": [{
                "dialog_id": "6b925c988495d224",
                "content": "不好意思，打扰您了，再见",
                "variate": []
            }],
            "action": 1,
            "master_process_id": "",
            "enable_logging": True,
            "other_config": {
                "intention_tag": "",
                "no_asr": 0,
                "nomatch_knowledge_ids": ""
            }
        }],
        "edge_setups": [{
            "node_id": "node-1765345629418-6861",
            "node_name": "主线流程二——介绍开场白",
            "route_map": {
                "9b16f3eded9c4a7e966594b8efefd5f7": "node-1765345710608-1633",
                "37d073d72185462693bd53cd3b536990": "node-1765345710608-1633",
                "b28dde69948744ae8fcce27a7c47c16a": "node-1765345824497-9287"
            },
            "enable_logging": True
        }, {
            "node_id": "node-1765345710608-1633",
            "node_name": "普通节点",
            "route_map": {
                "8c5bc4f5f61a41209cad51b13b69d44e": "node-1765346585901-6884",
                "bea0d9f799704d1a8595426e25908399": "node-1765346585901-6884",
                "189121c3dead4479b50a9445ee6eb8fa": "node-1765346610648-5912"
            },
            "enable_logging": True
        }]
    },
    "sort": 1
}]
knowledge_main_flow = []
global_configs = [
    {
        "context_type": 1,
        "answer": [{
            "reply_content_info": [{
                "dialog_id": "dialog_G1_1",
                "content": "再见了",
                "variate": []
            }],
            "action": 2,
            "next": "",
            "master_process_id": ""
        }],
        "intention_tag": "F",
        "status": 1,
        "enable_logging": True
    },
    {
        "context_type": 2,
        "answer": [{
            "reply_content_info": [{
                "dialog_id": "dialog_G1_1",
                "content": "再见了",
                "variate": []
            }],
            "action": 2,
            "next": "",
            "master_process_id": ""
        }],
        "intention_tag": "F",
        "status": 1,
        "enable_logging": True
    }
]