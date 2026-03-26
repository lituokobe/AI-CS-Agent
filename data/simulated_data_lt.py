agent_data = {
  "enable_nlp": 0,
  "nlp_threshold": 0.8,
  "intention_priority": 3,

  "use_llm": 1,
  "llm_name": "deepseek_llm",#"local_llm" "deepseek_llm" "glm_llm", "qwen_llm",
  "llm_threshold": 3,
  "llm_context_rounds": 2,
  "llm_role_description": "你是一个专业的家装平台的电话营销专员，你的任务是获取上海可能有装修意向的客户",
  "llm_background_info": "你现在正在沟通的都是可能会有装修需求的人，请尽量引导客户加微信",

  "vector_db_url": "http://127.0.0.1:19530",
  "collection_name" : "home_reno123"
}
chatflow_design = [
  {
    "sort" : 1,
    "main_flow_id" : "MF1",
    "main_flow_name" : "主流程一开场白",
    "main_flow_content" : {
      "starting_node_id" : "BN1",
      "base_nodes" : [
        {
          "node_id": "BN1",
          "node_name": "开场白",
          "reply_content_info": [{
              "dialog_id":"dialog_BN1",
              "content":"喂您好，（停顿2秒）我是${公司}的客服，近期我们针对${小区}业主举办了一个关于老房子翻新，毛坯房设计，和局部改动的实景样板房体验展，如果您近期或者明年有装修计划的话，都可以到现场免费的咨询了解一下",
              "variate":{
                "${公司}":{"content_type":2,"dynamic_var_set_type":1,"value":"巨峰科技","var_is_save":0},
                "${小区}":{"content_type":2,"dynamic_var_set_type":1,"value":"汤臣一品","var_is_save":0}
              }
          }],
          "intention_branches": [
            {
              "branch_id": "IB001",
              "branch_type": "REJECT",
              "branch_name": "拒绝",
              "branch_sort":7,
              "intention_ids": ["I003", "I008", "I010"]
            },
            {
              "branch_id": "IB002",
              "branch_type": "SURE",
              "branch_name": "肯定",
              "branch_sort":2,
              "intention_ids": ["I007", "I009", "I010"]
            },
            {
              "branch_id": "IB003",
              "branch_type": "CUSTOMER",
              "branch_name": "解释开场白",
              "branch_sort":1,
              "intention_ids": ["I006", "I010"]
            }
          ],
          "other_config": {
              "is_break": 1,
              "break_time": "0.0",
              "interrupt_knowledge_ids": "other_config_BN1",
              "wait_time": "3.5",
              "intention_tag": "other_config_BN1",
              "no_asr": 0,
              "nomatch_knowledge_ids": []
          },
          "enable_logging": True
        },
        {
          "node_id": "BN2",
          "node_name": "解释开场白",
          "reply_content_info": [{
              "dialog_id":"dialog_BN2",
              "content": "是这样的，近期在${地址}有个免费的家装实景体验展，现场您可以了解到智能家居，以及不同的装修风格，届时还有诸多明星前来助阵宣传，包括李宇春、蔡徐坤、刘欢，您看有没有兴趣来体验一下？",
              "variate":{
                "${地址}":{"content_type":2,"dynamic_var_set_type":1,"value":"上海国际会展中心","var_is_save":0}
              }
          }],
          "intention_branches": [
            {
              "branch_id": "IB004",
              "branch_type": "REJECT",
              "branch_name": "拒绝",
              "branch_sort":4,
              "intention_ids": ["I003", "I008", "I010"]
            },
            {
              "branch_id": "IB005",
              "branch_type": "SURE",
              "branch_name": "肯定",
              "branch_sort":2,
              "intention_ids": ["I007", "I009", "I010"]
            }
          ],
          "other_config": {
              "is_break": 1,
              "break_time": "0.0",
              "interrupt_knowledge_ids": "other_config_BN2",
              "wait_time": "3.5",
              "intention_tag": "other_config_BN2",
              "no_asr": 0,
              "nomatch_knowledge_ids": []
          },
          "enable_logging": True
        },
        {
          "node_id": "BN3",
          "node_name": "首次挽回",
          "reply_content_info": [{
              "dialog_id":"dialog_BN3",
              "content": "咱们现在不考虑也可以先过来了解一下目前装修市场的人工材料的费用。可以避免后期装修的一些猫腻和水分。现场时有最新风格的实景样板房可以免费参观体验，如果您家里近两年可能有装修的想法都可以先过来参观了解一下的。",
              "variate":{}
          }],
          "intention_branches": [
            {
              "branch_id": "IB006",
              "branch_type": "REJECT",
              "branch_name": "拒绝",
              "branch_sort":1,
              "intention_ids": ["I003", "I008", "I010"]
            },
            {
              "branch_id": "IB007",
              "branch_type": "SURE",
              "branch_name": "肯定",
              "branch_sort":2,
              "intention_ids": ["I007", "I009", "I010"]
            },
            {
              "branch_id": "IB007_1",
              "branch_type": "DEFAULT",
              "branch_name": "默认",
              "branch_sort":3,
              "intention_ids": []
            },
            {
              "branch_id": "IB007_2",
              "branch_type": "NO_REPLY",
              "branch_name": "客户无应答",
              "branch_sort":4,
              "intention_ids": []
            }
          ],
          "other_config": {
              "is_break": 1,
              "break_time": "0.0",
              "interrupt_knowledge_ids": "other_config_BN3",
              "wait_time": "3.5",
              "intention_tag": "other_config_BN3",
              "no_asr": 0,
              "nomatch_knowledge_ids": []
          },
          "enable_logging": True
        },
        {
          "node_id": "BN4",
          "node_name": "发送资料挽回",
          "reply_content_info": [{
              "dialog_id":"dialog_BN4",
              "content": "不管您来不来，如果近一年内有装修需求，我们都可以免费提供两本以上针对上海业主的装修宝典给您，一本是总结了近十年内装修业主的心得体会和装修猫腻，另一本是目前市面上热门的主辅材的品牌型号价格表。稍后让我们的家装顾问和您联系取人具体情况，您看可以吗？",
              "variate":{}
          }],
          "intention_branches": [
            {
              "branch_id": "IB008",
              "branch_type": "REJECT",
              "branch_name": "拒绝",
              "branch_sort":4,
              "intention_ids": ["I003", "I008", "I010"]
            },
            {
              "branch_id": "IB009",
              "branch_type": "SURE",
              "branch_name": "肯定",
              "branch_sort":2,
              "intention_ids": ["I007", "I009", "I010"]
            }
          ],
          "other_config": {
              "is_break": 1,
              "break_time": "0.0",
              "interrupt_knowledge_ids": "other_config_BN4",
              "wait_time": "3.5",
              "intention_tag": "other_config_BN4",
              "no_asr": 0,
              "nomatch_knowledge_ids": []
          },
          "enable_logging": True
        }
      ],
      "transfer_nodes" : [
        {
          "node_id": "TN1",
          "node_name": "肯定",
          "reply_content_info": [],
          "action": 3, # 1挂断 2跳转下一主线流程 3跳转指定主线流程
          "master_process_id": "MF2",
          "other_config": {
              "intention_tag": "Other_config_TN1",
			  "no_asr": 0,
			  "nomatch_knowledge_ids": []
          },
          "enable_logging": True
        },
        {
          "node_id": "TN2",
          "node_name": "挽回成功",
          "reply_content_info": [],
          "action": 3, # 1挂断 2跳转下一主线流程 3跳转指定主线流程
          "master_process_id": "MF3",
          "other_config": {
              "intention_tag": "Other_config_TN2",
			  "no_asr": 0,
			  "nomatch_knowledge_ids": []
          },
          "enable_logging": True
        },
        {
          "node_id": "TN3",
          "node_name": "客户拒绝",
          "reply_content_info": [{
              "dialog_id":"dialog_TN3",
              "content": "那不好意思打扰您了，以后我们有其他优惠活动再跟您取得联系，好吧？祝您生活愉快，再见。",
              "variate":{}
          }],
          "action": 1, # 1挂断 2跳转下一主线流程 3跳转指定主线流程
          "master_process_id": None,
          "other_config": {
              "intention_tag": "Other_config_TN3",
			  "no_asr": 0,
			  "nomatch_knowledge_ids": []
          },
          "enable_logging": True
        }
      ],
      "edge_setups": [
        {
          "node_id": "BN1",
          "node_name": "开场白",
          "route_map": {
            "IB001": "BN3",
            "IB002": "TN1",
            "IB003": "BN2"
          },
          "enable_logging": True
        },
        {
          "node_id": "BN2",
          "node_name": "解释开场白",
          "route_map": {
            "IB004": "BN3",
            "IB005": "TN1"
          },
          "enable_logging": True
        },
        {
          "node_id": "BN3",
          "node_name": "首次挽回",
          "route_map": {
            "IB006": "BN4",
            "IB007": "TN2",
            "IB007_1": "TN2",
            "IB007_2": "TN2",
          },
          "enable_logging": True
        },
        {
          "node_id": "BN4",
          "node_name": "发送资料挽回",
          "route_map": {
            "IB008": "TN3",
            "IB009": "TN2"
          },
          "enable_logging": True
        }
      ]
    }
  },
  {
    "sort" : 2,
    "main_flow_id" : "MF2",
    "main_flow_name" : "主流程二业务介绍",
    "main_flow_content" : {
      "starting_node_id" : "BN5",
      "base_nodes" : [
        {
          "node_id": "BN5",
          "node_name": "活动介绍",
          "reply_content_info": [
              {
                  "dialog_id":"dialog_BN5_1",
                  "content": "本次展会现场直接还原了在建工地样板间和本年度最新风格的整体实景样板房，对未来装修非常有借鉴意义。同时特邀嘉宾还将奉献精彩纷呈的表演，一展巨星风采。您看是不是来免费体验一下。",
                  "variate":{}
              },
              {
                  "dialog_id":"dialog_BN5_2",
                  "content": "这是一次非常精彩的的的展会。现场直接还原了在建工地样板间和本年度最新风格的整体实景样板房，对未来装修非常有借鉴意义。同时特邀嘉宾还将奉献精彩纷呈的表演，一展巨星风采。您绝对应该来体验一下！",
                  "variate":{}
              },
              {
                  "dialog_id":"dialog_BN5_3",
                  "content": "这场展会对未来装修非常有借鉴意义！现场直接还原了在建工地样板间和本年度最新风格的整体实景样板房，同时特邀嘉宾还将奉献精彩纷呈的表演，一展巨星风采。您不来太可惜了！",
                  "variate":{}
              },
          ],
          "intention_branches": [
            {
              "branch_id": "IB010",
              "branch_type": "REJECT",
              "branch_name": "拒绝",
              "branch_sort":1,
              "intention_ids": ["I003", "I008", "I010"]
            },
            {
              "branch_id": "IB011",
              "branch_type": "SURE",
              "branch_name": "肯定",
              "branch_sort":2,
              "intention_ids": ["I007", "I009", "I010"]
            }
          ],
          "other_config": {
              "is_break": 1,
              "break_time": "0.0",
              "interrupt_knowledge_ids": "other_config_BN5",
              "wait_time": "3.5",
              "intention_tag": "other_config_BN5",
              "no_asr": 0,
              "nomatch_knowledge_ids": ["K002", "K003", "K004"]
          },
          "enable_logging": True
        },
        {
          "node_id": "BN6",
          "node_name": "活动介绍资料发送挽回",
          "reply_content_info": [{
              "dialog_id": "dialog_BN6",
              "content": "不管您来不来，如果近一年内有装修需求，我们都可以免费提供两本以上针对上海业主的装修宝典给您，一本是总结了近十年内装修业主的心得体会和装修猫腻，另一本是目前市面上热门的主辅材的品牌型号价格表。稍后让我们的家装顾问和您联系取人具体情况，您看可以吗？",
              "variate":{}
          }],
          "intention_branches": [
            {
              "branch_id": "IB012",
              "branch_type": "REJECT",
              "branch_name": "拒绝",
              "branch_sort":1,
              "intention_ids": ["I003", "I008", "I010"]
            },
            {
              "branch_id": "IB013",
              "branch_type": "SURE",
              "branch_name": "肯定",
              "branch_sort":2,
              "intention_ids": ["I007", "I009", "I010"]
            }
          ],
          "other_config": {
              "is_break": 1,
              "break_time": "0.0",
              "interrupt_knowledge_ids": "other_config_BN6",
              "wait_time": "3.5",
              "intention_tag": "other_config_BN6",
              "no_asr": 0,
              "nomatch_knowledge_ids": []
          },
          "enable_logging": True
        }
      ],
      "transfer_nodes" : [
        {
          "node_id": "TN4",
          "node_name": "活动介绍沟通成功",
          "reply_content_info": [{
              "dialog_id": "dialog_TN4",
              "content": "您刚才说${客户输入},太棒了，我真替您感到高兴!",
              "variate":{
                "${客户输入}":{"content_type":2,"dynamic_var_set_type":2,"value":"","var_is_save":0}
              }
          }],
          "action": 2, # 1挂断 2跳转下一主线流程 3跳转指定主线流程
          "master_process_id": None,
          "other_config": {
              "intention_tag": "Other_config_TN4",
			  "no_asr": 0,
			  "nomatch_knowledge_ids": []
          },
          "enable_logging": True
        },
        {
          "node_id": "TN5",
          "node_name": "活动介绍客户拒绝",
          "reply_content_info": [{
              "dialog_id": "dialog_TN5",
              "content": "那好吧，以后我们有其他优惠活动再跟您联系。",
              "variate":{}
          }],
          "action": 1, # 1挂断 2跳转下一主线流程 3跳转指定主线流程
          "master_process_id": None,
          "other_config": {
              "intention_tag": "Other_config_TN5",
			  "no_asr": 0,
			  "nomatch_knowledge_ids": []
          },
          "enable_logging": True
        },
        {
          "node_id": "TN6",
          "node_name": "活动介绍挽回成功",
          "reply_content_info": [],
          "action": 3, # 1挂断 2跳转下一主线流程 3跳转指定主线流程
          "master_process_id": "MF3",
          "other_config": {
              "intention_tag": "Other_config_TN6",
			  "no_asr": 0,
			  "nomatch_knowledge_ids": []
          },
          "enable_logging": True
        }
      ],
      "edge_setups": [
        {
          "node_id": "BN5",
          "node_name": "活动介绍",
          "route_map": {
            "IB010": "BN6",
            "IB011": "TN4"
          },
          "enable_logging": True
        },
        {
          "node_id": "BN6",
          "node_name": "活动介绍资料发送挽回",
          "route_map": {
            "IB012": "TN5",
            "IB013": "TN6"
          },
          "enable_logging": True
        }
      ]
    }
  },
  {
    "sort" : 3,
    "main_flow_id" : "MF3",
    "main_flow_name" : "主流程三资料发放",
    "main_flow_content" : {
      "starting_node_id" : "BN7",
      "base_nodes" : [
        {
          "node_id": "BN7",
          "node_name": "资料发放",
          "reply_content_info": [{
              "dialog_id": "dialog_BN7",
              "content": "我们会给您免费提供一份资料，除了展会门票以外，还有一本装修宝典，这是由上百位业内专家，耗时五年倾力打造的装修巨作，被称为家装圣经。里面有装修的注意事项和一些装修的案例参考",
              "variate":{}
          }],
          "intention_branches": [
            {
              "branch_id": "IB014",
              "branch_type": "REJECT",
              "branch_name": "拒绝",
              "branch_sort":1,
              "intention_ids": ["I003", "I008", "I010"]
            },
            {
              "branch_id": "IB015",
              "branch_type": "SURE",
              "branch_name": "肯定",
              "branch_sort":2,
              "intention_ids": ["I007", "I009", "I010"]
            }
          ],
          "other_config": {
              "is_break": 1,
              "break_time": "0.0",
              "interrupt_knowledge_ids": "other_config_BN7",
              "wait_time": "3.5",
              "intention_tag": "other_config_BN7",
              "no_asr": 0,
              "nomatch_knowledge_ids": []
          },
          "enable_logging": True
        },
        {
          "node_id": "BN8",
          "node_name": "资料发送再次挽回",
          "reply_content_info": [{
              "dialog_id": "dialog_BN8",
              "content": "您真的不需要吗？这部家装圣经畅销海内外150个国家，被翻译成30多种语言，是联合国认定的非物质文化遗产。希望您再考虑一下。",
              "variate":{}
          }],
          "intention_branches": [
            {
              "branch_id": "IB016",
              "branch_type": "REJECT",
              "branch_name": "拒绝",
              "branch_sort":1,
              "intention_ids": ["I003", "I008", "I010"]
            },
            {
              "branch_id": "IB017",
              "branch_type": "SURE",
              "branch_name": "肯定",
              "branch_sort":2,
              "intention_ids": ["I007", "I009", "I010"]
            }
          ],
          "other_config": {
              "is_break": 1,
              "break_time": "0.0",
              "interrupt_knowledge_ids": "other_config_BN8",
              "wait_time": "3.5",
              "intention_tag": "other_config_BN8",
              "no_asr": 0,
              "nomatch_knowledge_ids": []
          },
          "enable_logging": True
        }
      ],
      "transfer_nodes" : [
        {
          "node_id": "TN7",
          "node_name": "发资料沟通成功",
          "reply_content_info": [{
              "dialog_id": "dialog_TN7",
              "content": "Wonderful! 稍后我们的家装顾问会和您电话联系，确认具体情况，请您保持手机畅通。祝您生活愉快，再见",
              "variate":{}
          }],
          "action": 1, # 1挂断 2跳转下一主线流程 3跳转指定主线流程
          "master_process_id": None,
          "other_config": {
              "intention_tag": "Other_config_TN7",
			  "no_asr": 0,
			  "nomatch_knowledge_ids": []
          },
          "enable_logging": True
        },
        {
          "node_id": "TN8",
          "node_name": "发资料客户拒绝",
          "reply_content_info": [{
              "dialog_id": "dialog_TN8",
              "content": "真的太遗憾了，为您错过一次阅读家装圣经的机会而感到惋惜，Adios!",
              "variate":{}
          }],
          "action": 1, # 1挂断 2跳转下一主线流程 3跳转指定主线流程
          "master_process_id": None,
          "other_config": {
              "intention_tag": "Other_config_TN8",
			  "no_asr": 0,
			  "nomatch_knowledge_ids": []
          },
          "enable_logging": True
        }
      ],
      "edge_setups": [
        {
          "node_id": "BN7",
          "node_name": "资料发放",
          "route_map": {
            "IB014": "BN8",
            "IB015": "TN7"
          },
          "enable_logging": True
        },
        {
          "node_id": "BN8",
          "node_name": "资料发送再次挽回",
          "route_map": {
            "IB016": "TN8",
            "IB017": "TN7"
          },
          "enable_logging": True
        }
      ]
    }
  },
  {
    "sort" : 4,
    "main_flow_id" : "MF4",
    "main_flow_name" : "主流程兜底询问",
    "main_flow_content" : {
      "starting_node_id" : "BN9",
      "base_nodes" : [
        {
          "node_id": "BN9",
          "node_name": "兜底询问",
          "reply_content_info": [{
              "dialog_id": "dialog_BN9",
              "content": "不好意思，刚才没听清，我们会给您免费提供一份资料，您装修时肯定用得到！稍后由我们家装顾问和您联系确认具体情况，你看可以吗？",
              "variate":{}
          }],
          "intention_branches": [
            {
              "branch_id": "IB018",
              "branch_type": "REJECT",
              "branch_name": "拒绝",
              "branch_sort":1,
              "intention_ids": ["I003", "I008", "I010"]
            },
            {
              "branch_id": "IB019",
              "branch_type": "SURE",
              "branch_name": "肯定",
              "branch_sort":2,
              "intention_ids": ["I007", "I009", "I010"]
            }
          ],
          "other_config": {
              "is_break": 1,
              "break_time": "0.0",
              "interrupt_knowledge_ids": "other_config_BN9",
              "wait_time": "3.5",
              "intention_tag": "other_config_BN9",
              "no_asr": 0,
              "nomatch_knowledge_ids": ["K002"]
          },
          "enable_logging": True
        }
      ],
      "transfer_nodes" : [
        {
          "node_id": "TN9",
          "node_name": "肯定",
          "reply_content_info": [{
              "dialog_id": "dialog_TN9",
              "content": "非常好！这是兜底询问的主流程。你在这个位置被挽回成功了，简直是个奇迹。",
              "variate":{}
          }],
          "action": 3, # 1挂断 2跳转下一主线流程 3跳转指定主线流程
          "master_process_id": "MF3",
          "other_config": {
              "intention_tag": "Other_config_TN9",
			  "no_asr": 0,
			  "nomatch_knowledge_ids": []
          },
          "enable_logging": True
        },
        {
          "node_id": "TN10",
          "node_name": "客户拒绝",
          "reply_content_info": [{
              "dialog_id": "dialog_TN10",
              "content": "不好意思，打扰您了，我们有缘再会!",
              "variate":{}
          }],
          "action": 2, # 1挂断 2跳转下一主线流程 3跳转指定主线流程
          "master_process_id": None,
          "other_config": {
              "intention_tag": "Other_config_TN10",
			  "no_asr": 0,
			  "nomatch_knowledge_ids": []
          },
          "enable_logging": True
        }
      ],
      "edge_setups": [
        {
          "node_id": "BN9",
          "node_name": "兜底询问",
          "route_map": {
            "IB018": "TN10",
            "IB019": "TN9"
          },
          "enable_logging": True
        }
      ]
    }
  },
  {
    "sort" : 5,
    "main_flow_id" : "MF5",
    "main_flow_name" : "主流程兜底挂断",
    "main_flow_content" : {
      "starting_node_id" : "TN11",
      "base_nodes" : [],
      "transfer_nodes" : [
        {
          "node_id": "TN11",
          "node_name": "兜底挂断",
          "reply_content_info": [{
              "dialog_id": "dialog_TN11",
              "content": "嗯嗯，稍后我们的家装顾问会和您电话联系，确认具体情况，请您保持手机畅通。祝您生活愉快，再见",
              "variate":{}
          }],
          "action": 2, # 1挂断 2跳转下一主线流程 3跳转指定主线流程
          "master_process_id": None,
          "other_config": {
              "intention_tag": "Other_config_TN11",
			  "no_asr": 0,
			  "nomatch_knowledge_ids": []
          },
          "enable_logging": True
        }
      ],
      "edge_setups": [
      ]
    }
  }
]
global_configs = [
  {
    "context_type": 1, # 1客户无应答模块 2ai未识别模块 3噪音处理模块
    "answer": [
      {
        "reply_content_info": [{
              "dialog_id":"dialog_G1_1",
              "content":"你怎么不说话，说话呀",
              "variate":{}
          }],
        "action": 1, # 1等待用户回复  2挂断  3跳转主流程,
        "next": None, # -1原主线节点 -2原主线流程  3指定主线流程
        "master_process_id": None
      },
      {
        "reply_content_info": [{
              "dialog_id":"dialog_G1_2",
              "content":"我求求你说一句话吧",
              "variate":{}
          }],
        "action": 3, # 1等待用户回复  2挂断  3跳转主流程,
        "next": -1, # -1原主线节点 -2原主线流程  3指定主线流程
        "master_process_id": None
      },
      {
        "reply_content_info": [{
              "dialog_id":"dialog_G1_3",
              "content":"你不说话我就再重复一遍！",
              "variate":{}
          }],
        "action": 3, # 1等待用户回复  2挂断  3跳转主流程,
        "next": -2, # -1原主线节点 -2原主线流程  3指定主线流程
        "master_process_id": None
      },
      {
        "reply_content_info": [{
              "dialog_id":"dialog_G1_4",
              "content":"你不说话我挂了昂",
              "variate":{}
          }],
        "action": 2, # 1等待用户回复  2挂断  3跳转主流程,
        "next": None, # -1原主线节点 -2原主线流程  3指定主线流程
        "master_process_id": None
      }
    ],
    "intention_tag": "A",
    "status": 1,
    "enable_logging": True
  },
  {
    "context_type": 2, # 1客户无应答模块 2ai未识别模块 3噪音处理模块
    "answer": [
      {
        "reply_content_info": [{
              "dialog_id":"dialog_G2_1",
              "content":"您竟然说${客户输入}，真的太出乎我意料了！",
              "variate":{
                "${客户输入}":{"content_type":2,"dynamic_var_set_type":2,"value":"","var_is_save":0}
              }
          }],
        "action": 3, # 1等待用户回复  2挂断  3跳转主流程,
        "next": 3, # -1原主线节点 -2原主线流程  3指定主线流程
        "master_process_id": "MF4"
      },
      {
        "reply_content_info": [{
              "dialog_id":"dialog_G2_2",
              "content":"您是不是在说${客户输入}，你没事吧？",
              "variate":{
                "${客户输入}":{"content_type":2,"dynamic_var_set_type":2,"value":"","var_is_save":0}
              }
          }],
        "action": 3, # 1等待用户回复  2挂断  3跳转主流程,
        "next": -1, # -1原主线节点 -2原主线流程  3指定主线流程
        "master_process_id": None
      },
      {
        "reply_content_info": [{
              "dialog_id":"dialog_G2_3",
              "content":"不是，你这人怎么胡说八道啊？",
              "variate":{}
          }],
        "action": 1, # 1等待用户回复  2挂断  3跳转主流程,
        "next": None, # -1原主线节点 -2原主线流程  3指定主线流程
        "master_process_id": None
      }
    ],
    "intention_tag": "A",
    "status": 1,
    "enable_logging": True
  }
]
intentions = [
  {
    "intention_id": "I001",
    "intention_name": "微信号码就这些",
    "keywords": [
      "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "幺", "12345678",
      "零", "一", "二", "三", "四", "五", "六", "七", "八", "九", "32859617",
      "就是这个号", "就这个", "没了", "就是这些", "就是这些号", "没有了",
      "你直接加就行", "就这些", "你加吧"
    ],
    "semantic": [],
    "llm_description": ["用户报完微信"]
  },
  {
    "intention_id": "I002",
    "intention_name": "直接报微信",
    "keywords": [
      "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "幺",
      "零", "一", "二", "三", "四", "五", "六", "七", "八", "九",
      "我说你记", "报一下", "记一下"
    ],
    "semantic": [],
    "llm_description": ["用户直接说出了自己的微信"]
  },
  {
    "intention_id": "I003",
    "intention_name": "客户拒绝",
    "keywords": [
      "^不是", "再见$", "(牛|狗|猪)", "没(.*)欲望", "(\w+)先生"
    ],
    "semantic":  [
      "不要加我的微信", "这个我不需要",
      "没有这个想法", "我微信都加满了",  "没钱用不起",
      "我没有这方面的需求", "我不需要这个", "加我微信干什么",
      "不想加微信", "谁让你加我微信",
      "我不用微信", "这个我用不着", "我微信加不了人",
      "你加我的微信干啥", "有需要我跟你联系", "别加我的微信", "我都弄好了",
      "不是很需要", "你加我微信干什么", "我没有这方面的需要",
      "我用不着", "不弄这个", "我不要", "我不需要",
      "我不用", "不需要介绍", "你别说了", "不要给我介绍了", "别说了",
      "没要装修", "最近没这个打算的。", "没有装修的打算", "不需要装修", "目前没有计划",
      "我目前不需要装修", "我明年才要装修", "明年再说"
    ],
    "llm_description": ["客户拒绝了当前的要求"]
  },
  {
    "intention_id": "I004",
    "intention_name": "手机号不是微信",
    "keywords": [
      "不可以加上","不是这个号码", "打的哪个电话", "手机不是微信",
      "另外一个号", "打的哪个号码", "不是微信", "另外一个微信", "不是我的微信号",
      "手机没有微信", "另外一个手机", "不是微信号", "不是这个",
      "加不了", "你加这个", "号不是微信", "另外一个", "这个手机不是", "另外一个号码", "这个不是微信",
      "这个号码不能加", "不这个号", "你加不上这个号", "号码不是这个", "不是你打的这个",
      "另一个微信", "另一个号码", "手机号没有微信", "手机号不是微信",
      "这个加不了", "手机号不是我微信号", "不是我微信", "不是这个微信号码",
      "打得哪个电话", "不是这个手机", "我报一个", "另一个手机", "不是我的微信",
      "号没有微信", "告诉你个号", "手机号不是微信号"
    ],
    "semantic": [
      "这个号码不能加", "手机号没有微信", "不是这个手机", "另外一个微信",
      "不是这个微信号码", "打得哪个号码", "手机号不是我微信号", "不是我的微信",
      "手机没有微信", "这个加不了", "不是我的微信号", "打的哪个号码",
      "手机不是微信", "手机号不是微信号", "号码不对", "号码不是这个",
      "另外一个号", "告诉你个号", "手机号不是微信", "不是你打的这个",
      "不可以加上", "这个不是微信", "不是微信号", "加不了，我给你一个号"
    ],
    "llm_description": ["用户表示手机号不是自己的微信"]
  },
  {
    "intention_id": "I005",
    "intention_name": "肯定手机号是微信",
    "keywords": [
      "发一下", "加下微信", "是手机号", "这也是我的微信号",  "发过来",
      "手机号是微信", "是这个手机号", "加下我", "手机就是微信", "你加我微信",
      "是这个手机", "电话号码", "加我吧", "给我微信", "就是这个号码",
      "是我手机号", "加我个微信", "微信号是手机", "手机号就是微信号", "微信上说",
      "微信号就是手机","手机就是我微信", "发个微信", "就是这个手机", "加我微信",
      "是我微信号", "就是手机号", "加我的", "微信就是", "资料微信发给我", "这个手机就是",
      "加下这个手机", "你发我", "你加吧", "加我", "本机号", "就这个号"
    ],
    "semantic": [
      "就这个手机号", "就是这手机", "你加这个手机号就可以", "我微信就是这个手机号",
      "你就加这个手机号", "就是这个号", "可以没问题", "微信号就是手机", "微信就是这个手机号",
      "是我的微信号", "就是的加吧", "好的那你发给我看下吧", "就是这个手机",
      "行那你发吧", "就是本机号码", "你直接加就行", "就是这个微信",
      "好的那你发吧", "行的加吧", "好的好的", "就是这个号码",
      "手机号就是微信号", "没错是的你加吧", "是的你直接加吧", "直接发就行"
    ],
    "llm_description": ["用户确认手机号就是自己的微信"]
  },
  {
    "intention_id": "I006",
    "intention_name": "解释开场白",
    "keywords": [
      "怎么了", "打电话干什么", "你打电话干什么", "你什么事情", "你干啥",
      "干嘛的", "什么事", "啥事", "打电话做什么", "什么展会", "你是谁",
      "我听不清", "推销什么", "你们做什么的", "有什么事情", "干嘛", "搞什么",
      "有什么事", "这是哪里", "你做什么的", "你找谁"
    ],
    "semantic": [
      "你好。什么意思", "没听清你说的什么", "什么意思", "你说的我没弄明白",
      "你说啥", "你说的什么东西", "哪里。什么东西。", "你有什么事情吗",
      "再说一遍", "没听懂你在说什么", "你是做什么的", "怎么？",
      "你讲的什么东西", "没听懂", "什么东西", "你好，什么意思",
      "你说什么我没听懂", "不知道你在说什么", "哪里。什么意思。"
    ],
    "llm_description": ["用户需要明白为什么打通电话或者为什么在和你对话"]
  },
  {
    "intention_id": "I007",
    "intention_name": "肯定",
    "keywords": [
      "发我信息吧", "你加我微信上说把", "微信号就是手机", "好呢", "加下微信",
      "微信沟通", "你加吧", "资料用微信发给我", "你加我下微信吧", "你加我本机号",
      "加我的电话", "得嘞", "发我个短信", "加我个微信", "好哒", "我加你",
      "微信发我","好哇好哇", "发短信给我说", "我自己操作吧", "手机号给我报下",
      "你加我的", "手机号就是我微信", "资料微信发给我",
      "你加下我微信", "短信发我吧", "那你加吧", "发个信息给我", "我加你微信",
      "这个手机就是我微信", "短信沟通", "给我发个短信", "好哇好哇",
      "加我微信吧", "直接加", "行啊", "给我发个产品的介绍", "我直接加你",
      "给我发短信", "给我发个信息", "OK", "好的啊", "可以的呀", "好的",
      "要装", "好勒", "晚点给我打", "等一会打", "就是这个账号", "另一个手机",
      "寄给我", "过一会再说", "寄吧", "你发吧", "Ok", "发吧",
      "没问题", "我要", "再联系", "嗯可以", "就是这个手机", "嗯寄吧",
      "行的", "行行行", "太好了", "免费就要"
    ],
    "semantic": [
      "有这方面需求的", "有这方面想法", "我家房子需要翻新", "等我有空的时候去看下",
      "我正好需要装修", "我有时间过去看下", "到时候我去现场看下", "我正好有房子需要装修",
      "我正好有房子要装修。", "我有房子需要翻新", "我有房子需要装修", "我家里正好有个老房子",
      "那你快递一份资料吧", "你给我邮寄一份吧", "把资料发给我", "让他加我微信说",
      "资料发我微信", "你给我寄一份吧"
    ],
    "llm_description": ["用户表示肯定"]
  },
  {
    "intention_id": "I008",
    "intention_name": "没时间",
    "keywords": [
      "没时间", "现在没空", "在上班", "来不及", "时间不够", "很忙",
      "到时候看", "没有空", "我要上班", "时间长", "太晚", "没有时间",
      "有事", "有没有时间", "赶不上", "不想去", "没空", "太长", "不确定",
      "我时间", "我没空", "去不了", "可能有事"
    ],
    "semantic": [
      "我现在忙着呢", "我没有时间跟你说这个", "我马上有事没时间接你电话", "我正在开会",
      "我没功夫跟你说", "我在打麻将", "我在国道上", "我没有功夫接你电话",
      "我现在有事情要处理", "我现在在开车", "我马上要开会", "我在打游戏",
      "我在省道上", "没空去", "不好意思我现在有事", "我在高架上",
      "我现在有事", "我没时间听你说话", "我在开车没办法接电话", "我现在在高速上"
    ],
    "llm_description": ["用户没有时间"]
  },
  {
    "intention_id": "I009",
    "intention_name": "发资料",
    "keywords": [
      "怎么联系你", "发邮件", "发地址给我", "发邮箱", "发消息",
      "资料", "发个地址", "发短信", "发一下", "短信发我",
      "发个位置", "发我这", "发我信息", "门票发我",
      "联系方式", "短信", "发位置", "发给我", "给我发短信", "发信息",
      "发个短信给我", "发条信息", "你电话多少", "发资料", "发份资料",
      "地址发给我", "地址发我", "发我手机", "发到我手机", "短信给我",
      "发我电话", "发我信息吧", "发我短信", "发个短信"
    ],
    "semantic": [
      "发个资料给我", "发我个短信", "发资料给我看一下",
      "发个信息给我", "发短信给我说", "我先看一下资料",
      "发个短信给我看看", "发我个信息", "给我发资料", "资料发到我手机上",
      "先发下资料给我", "给我发个短信", "给我发个信息",
      "你发给我看看", "我看下资料", "给我发点资料", "短信发给我",
      "有没有资料发我看看", "短信发我吧", "给我发短信", "资料短信发给我",
      "那你快递一份资料吧", "你给我邮寄一份吧", "把资料发给我", "让他加我微信说",
      "资料发我微信", "你给我寄一份吧"
    ],
    "llm_description": ["用户要求把资料发过来"]
  },
  {
    "intention_id": "I010",
    "intention_name": "很可爱",
    "keywords": [
      "我很可爱", "我很帅", "我很漂亮", "我是万人迷"
    ],
    "semantic": [
      "我好可爱", "我好帅", "我好漂亮", "你见过比我更可爱的吗", "还有人比我更可爱吗",
      "还有人比我更帅吗", "还有人比我更漂亮吗", "我是最可爱的", "我是最帅的", "我是最漂亮的"
    ],
    "llm_description": ["用户表示自己很可爱"]
  }
]
knowledge = [
  {
    "intention_id": "K001",
    "intention_name": "用户要求讲重点",
    "knowledge_type": 1,
    "keywords": [
      "讲重点", "说快点", "你讲快点", "快点说"
    ],
    "semantic": ["没听懂你做什么的", "你简单说下就可以了", "你说重点的", "你简单说说就行", "你快点说完"],
    "llm_description": ["用户要求讲重点"],
    "answer_type": 1, #1单轮回答 2多轮回答
    "answer": [ # 单轮回答时是话术json, 多轮回答是工作流id的字符串
      {
        "reply_content_info": [{
              "dialog_id":"dialog_K001",
              "content":"不好意思呀 因为我这边是公司新来的业务员 可能对一些业务细节还不太清楚 我稍后安排公司的家装顾问 让他帮您详细介绍一下可以吗?",
              "variate":{}
          }],
        "action": 1, # 1等待用户回复  2挂断  3跳转主流程,
        "next": None, # -1原主线节点 -2原主线流程  3指定主线流程
        "master_process_id": None
      }
    ],
    "other_config": {
        "is_break": 0,
        "break_time": "2.0",
        "wait_time": "3.5",
        "intention_tag": "0",
        "no_asr": 0,
        "match_num": 1
    },
    "enable_logging": True
  },
  {
    "intention_id": "K002",
    "intention_name": "你叫什么名字",
    "knowledge_type": 1,
    "keywords": [
      "称呼", "贵姓", "姓什么"
    ],
    "semantic": [
      "你叫什么名字", "你名字叫啥", "怎么称呼你", "请问你贵姓", "怎么称呼", "怎么称呼您"
    ],
    "llm_description": ["用户询问姓名"],
    "answer_type": 1, #1单轮回答 2多轮回答
    "answer": [ # 单轮回答时是话术json, 多轮回答是工作流id的字符串
      {
        "reply_content_info": [{
              "dialog_id":"dialog_K002_1",
              "content":"您叫我小杜就可以了 我一会发个短信到您手机上 上面有我的信息的 后面如果您有不清楚的 随时联系我就可以了",
              "variate":{}
          }],
        "action": 3, # 1等待用户回复  2挂断  3跳转主流程,
        "next": -1, # -1原主线节点 -2原主线流程  3指定主线流程
        "master_process_id": None
      },
      {
        "reply_content_info": [{
              "dialog_id":"dialog_K002_2",
              "content":"我的名字叫小杜，跟我念一遍！大声点我听不见！",
              "variate":{}
          }],
        "action": 1, # 1等待用户回复  2挂断  3跳转主流程,
        "next": None, # -1原主线节点 -2原主线流程  3指定主线流程
        "master_process_id": None
      },
      {
        "reply_content_info": [{
              "dialog_id":"dialog_K002_3",
              "content":"我就是小杜，一个纯粹的我，一个脱离低级趣味的我。我就是我，我敢比。",
              "variate":{}
          }],
        "action": 3, # 1等待用户回复  2挂断  3跳转主流程,
        "next": 3, # -1原主线节点 -2原主线流程  3指定主线流程
        "master_process_id": "MF1"
      }
    ],
    "other_config": {
        "is_break": 0,
        "break_time": "2.0",
        "wait_time": "3.5",
        "intention_tag": "0",
        "no_asr": 0,
        "match_num": 6
    },
    "enable_logging": True
  },
  {
    "intention_id": "K003",
    "intention_name": "质疑号码来源",
    "knowledge_type": 1,
    "keywords": [
      "怎么有我手机", "在哪看到", "哪来的手机号", "怎么找到我", "从哪弄个电话号码", "怎么知道我这个手机",
      "怎么找到我的电话", "哪个人卖你的信息", "你是从哪看到的呀", "怎么得到的手机", "我问你从哪里看到我的电话的",
      "啊我这电话咋弄嘞"
    ],
    "semantic": [
      "你为什么会有我的电话号码", "我的电话你们是哪来的", "你怎么知道我的电话号码的", "你是从哪搞到我电话",
      "哪里来的我的号码", "哪里买的我的号码", "你们在哪里得到我的信息", "怎么得到的我的电话", "你从哪里得到的电话",
      "谁给你的我的电话", "我手机号码你哪来的", "你是从哪搞到我手机号"
    ],
    "llm_description": ["客户问你怎么知道我的号码的"],
    "answer_type": 1, #1单轮回答 2多轮回答
    "answer": [ # 单轮回答时是话术json, 多轮回答是工作流id的字符串
      {
        "reply_content_info": [{
              "dialog_id":"dialog_K003",
              "content":"咱们这边是不显示您个人信息的，我们是针对整个上海业主做一个活动通知。",
              "variate":{}
          }],
        "action": 3, # 1等待用户回复  2挂断  3跳转主流程,
        "next": -2, # -1原主线节点 -2原主线流程  3指定主线流程
        "master_process_id": None
      }
    ],
    "other_config": {
        "is_break": 0,
        "break_time": "2.0",
        "wait_time": "3.5",
        "intention_tag": "0",
        "no_asr": 0,
        "match_num": None
    },
    "enable_logging": True
  },
  {
    "intention_id": "K004",
    "intention_name": "活动内容",
    "knowledge_type": 2,
    "keywords": [
      "能了解到什么", "能展示什么", "展示什么", "什么展", "展览什么", "关于哪方面", "什么展会", "展会内容", "啥展览",
      "哪些活动", "展出内容", "展会", "能看到什么", "展出什么", "展览啥", "什么活动", "了解什么", "优惠活动","活动内容"
    ],
    "semantic": [
      "是什么样子的展会", "展会里有什么活动", "什么活动内容", "展览什么东西", "展览些什么展品", "你们展会是展览什么的",
      "是关于什么的展览", "有哪些展品", "展览上有什么优惠活动", "展会是展示什么东西的", "展会有哪些内容", "展示什么东西"
    ],
    "llm_description": ["客户问展会内容"],
    "answer_type": 1, #1单轮回答 2多轮回答
    "answer": [ # 单轮回答时是话术json, 多轮回答是工作流id的字符串
      {
        "reply_content_info": [{
              "dialog_id": "dialog_K004",
              "content": "",
              "variate":{}
          }],
        "action": 3, # 1等待用户回复  2挂断  3跳转主流程,
        "next": 3, # -1原主线节点 -2原主线流程  3指定主线流程
        "master_process_id": "MF2"
      }
    ],
    "other_config": {
        "is_break": 0,
        "break_time": "2.0",
        "wait_time": "3.5",
        "intention_tag": "0",
        "no_asr": 0,
        "match_num": 10
    },
    "enable_logging": True
  },
  {
    "intention_id": "K005",
    "intention_name": "换人联系",
    "knowledge_type": 3,
    "keywords": [
      "直接跟我说", "就要你说", "答非所问", "直接跟我讲"
    ],
    "semantic":  [
      "经理联系我", "让你们领导来说", "你们经理跟我联系", "你的回答太差了", "直接经理跟我说",
      "我不跟机器人说", "让你们经理联系我", "换个人和我说", "换你们领导联系", "让你们经理来说",
      "让真人联系", "领导联系", "你的业务能力太差了", "直接让你们经理", "不能跟你沟通", "你一点都不专业",
      "换人跟我说", "你怎么什么都不懂", "不能给我介绍", "你业务都不熟练啊", "你业务不专业", "就你跟我讲就好了",
      "换你们老师给我打", "一点都不专业", "换你们经理给我打", "你到不知道你打什么电话", "我不想跟机器人聊天",
      "换你们经理给我聊", "你怎么一问三不知啊", "你业务知识不行啊", "让活人给我打", "你是新来的业务员吗",
      "换个经验丰富的", "你是新来的吗", "你直接换真人给我联系吧", "直接让经理说", "你转人工", "不想跟机器废话",
      "你怎么什么都不知道", "你的业务能力怎么这么差", "你这边能换个人给我打电话吗", "换真人给我沟通", "不想跟机器人沟通",
      "换有经验的跟我说", "你不知道就换人跟我说", "让你们老板跟我说", "我不想跟机器人说话", "你不会介绍就换个人行吗"
    ],
    "llm_description": ["用户要求换一个真人或者联系经理来服务"],
    "answer_type": 1, #1单轮回答 2多轮回答
    "answer": [ # 单轮回答时是话术json, 多轮回答是工作流id的字符串
      {
        "reply_content_info": [{
              "dialog_id": "dialog_K005",
              "content": "不好意思，稍后将由我们具体负责相关业务的同事来联系您。祝您生活愉快，再见！",
              "variate":{}
          }],
        "action": 2, # 1等待用户回复  2挂断  3跳转主流程,
        "next": None, # -1原主线节点 -2原主线流程  3指定主线流程
        "master_process_id": None
      }
    ],
    "other_config": {
        "is_break": 0,
        "break_time": "2.0",
        "wait_time": "3.5",
        "intention_tag": "0",
        "no_asr": 0,
        "match_num": 5
    },
    "enable_logging": True
  },
  {
    "intention_id": "K006",
    "intention_name": "加微信",
    "knowledge_type": 2,
    "keywords": [
      "微信发给我", "加个微信", "微信说", "微信发我", "加我微信", "微信聊吧", "直接加", "加微信说",
      "加微信", "直接加我"
    ],
    "semantic":  [
      "你加个微信发给我看看", "你直接加我这个微信", "你发个微信给我看下", "你加一下我的微信", "你加我这个号码微信",
      "你加个微信发给我", "加我这个微信", "本机号码就是微信", "先加一个我微信", "你加下我微信", "你加我微信发给我看看",
      "我来加你微信", "直接加我微信", "你微信号是多少", "发我个短信", "有资料吗发给我看看", "你加个微信，加个微信去聊"
    ],
    "llm_description": ["客户主动要加微信，或者主动要在微信发资料给他"],
    "answer_type": 2, #1单轮回答 2多轮回答
    "answer": "MF_wechat", # 单轮回答时是话术json, 多轮回答是工作流id的字符串
    "other_config": {
        "is_break": 0,
        "break_time": "2.0",
        "wait_time": "3.5",
        "intention_tag": "0",
        "no_asr": 0,
        "match_num": 10
    },
    "enable_logging": True
  }
]
knowledge_main_flow = [
  {
    "main_flow_id" : "MF_wechat",
    "main_flow_name" : "知识库流程加微信",
    "main_flow_content" : {
      "starting_node_id" : "BN_wechat1",
      "base_nodes" : [
        {
          "node_id": "BN_wechat1",
          "node_name": "加微信",
          "reply_content_info": [
              {
                  "dialog_id":"dialog_BN_wechat1_1",
                  "content":"真的吗? 您刚才说${客户输入}，好高兴可以加您的微信。我马上加，有什么不清楚的地方，可以随时联系我。",
                  "variate":{
                      "${客户输入}":{"content_type":2,"dynamic_var_set_type":2,"value":"","var_is_save":0}
                  }
              },
              {
                  "dialog_id":"dialog_BN_wechat1_2",
                  "content":"根据您刚才说的${客户输入}，那我就欣然接受，马上加你微信。",
                  "variate":{
                      "${客户输入}":{"content_type":2,"dynamic_var_set_type":2,"value":"","var_is_save":0}
                  }
              },
              {
                  "dialog_id": "dialog_BN_wechat1_3",
                  "content": "我已经迫不及待的要加你的微信了！",
                  "variate": {}
              }
          ],
          "intention_branches": [
            {
              "branch_id": "IB_wechat1",
              "branch_type": "REJECT",
              "branch_name": "拒绝",
              "branch_sort":1,
              "intention_ids": ["I003", "I008", "I010"]
            },
            {
              "branch_id": "IB_wechat2",
              "branch_type": "SURE",
              "branch_name": "肯定",
              "branch_sort":2,
              "intention_ids": ["I007", "I009", "I010"]
            }
          ],
          "other_config": {
              "is_break": 1,
              "break_time": "0.0",
              "interrupt_knowledge_ids": "other_config_BN_wechat1",
              "wait_time": "3.5",
              "intention_tag": "other_config_BN_wechat1",
              "no_asr": 0,
              "nomatch_knowledge_ids": []
          },
          "enable_logging": True
        },
        {
          "node_id": "BN_wechat2",
          "node_name": "再次请求加微信",
          "reply_content_info": [{
              "dialog_id":"dialog_BN_wechat2",
              "content":"怎么又不加了？害羞了吗，你个小可爱。",
              "variate":{}
          }],
          "intention_branches": [
            {
              "branch_id": "IB_wechat3",
              "branch_type": "REJECT",
              "branch_name": "拒绝",
              "branch_sort":1,
              "intention_ids": ["I003", "I008"]
            },
            {
              "branch_id": "IB_wechat4",
              "branch_type": "SURE",
              "branch_name": "肯定",
              "branch_sort":2,
              "intention_ids": ["I007", "I009"]
            }
          ],
          "other_config": {
              "is_break": 1,
              "break_time": "0.0",
              "interrupt_knowledge_ids": "other_config_BN_wechat2",
              "wait_time": "3.5",
              "intention_tag": "other_config_BN_wechat2",
              "no_asr": 0,
              "nomatch_knowledge_ids": []
          },
          "enable_logging": True
        }
      ],
      "transfer_nodes": [
         {
          "node_id": "TN_wechat3",
          "node_name": "加微信挽留成功",
          "reply_content_info": [{
              "dialog_id":"dialog_TN_wechat3",
              "content":"你被我感动地反悔了，又想加我微信啦！",
              "variate":{}
          }],
          "action": 0, # 0等待用户回复 1挂断 3跳转主流程
          "next": None, # -1原主线节点 -2原主线流程  others指定主线流程
          # "master_process_id": None,
          "other_config": {
              "intention_tag": "Other_config_TN_wechat2",
			  "no_asr": 0,
			  "nomatch_knowledge_ids": []
          },
          "enable_logging": True
        },
        {
          "node_id": "TN_wechat2",
          "node_name": "加微信肯定",
          "reply_content_info": [{
              "dialog_id":"dialog_TN_wechat2",
              "content":"我已发送添加邀请，您注意通过一下，祝您生活愉快，再见!",
              "variate":{}
          }],
          "action": 1, # 0等待用户回复 1挂断 3跳转主流程
          "next": None, # -1原主线节点 -2原主线流程  others指定主线流程
          # "master_process_id": None,
          "other_config": {
              "intention_tag": "Other_config_TN_wechat2",
			  "no_asr": 0,
			  "nomatch_knowledge_ids": []
          },
          "enable_logging": True
        },
        {
          "node_id": "TN_wechat1",
          "node_name": "加微信客户拒绝",
          "reply_content_info": [{
              "dialog_id":"dialog_TN_wechat1",
              "content":"那不好意思，我就先不加您微信了，拜拜了您嘞",
              "variate":{}
          }],
          "action": 3, # 0等待用户回复 1挂断 3跳转主流程
          "next": "MF3", # -1原主线节点 -2原主线流程  others指定主线流程
          # "master_process_id": "MF3",
          "other_config": {
              "intention_tag": "Other_config_TN_wechat1",
			  "no_asr": 0,
			  "nomatch_knowledge_ids": []
          },
          "enable_logging": True
        }
      ],
      "edge_setups": [
        {
          "node_id": "BN_wechat1",
          "node_name": "加微信",
          "route_map": {
            "IB_wechat1": "BN_wechat2",
            "IB_wechat2": "TN_wechat2"
          },
          "enable_logging": True
        },
        {
          "node_id": "BN_wechat2",
          "node_name": "再次请求加微信",
          "route_map": {
            "IB_wechat3": "TN_wechat1",
            "IB_wechat4": "TN_wechat3"
          },
          "enable_logging": True
        }
      ]
    }
  }
]