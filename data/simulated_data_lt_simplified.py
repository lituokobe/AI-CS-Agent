agent_data = {
  "enable_nlp": 1,
  "nlp_threshold": 0.8,
  "intention_priority": 3,

  "use_llm": 0,
  "llm_name": "deepseek_llm", #"glm_llm", #"qwen_llm",
  "llm_threshold": 3,
  "llm_context_rounds": 2,
  "llm_role_description": "你是一个专业的家装平台的电话营销专员，你的任务是获取上海可能有装修意向的客户",
  "llm_background_info": "你现在正在沟通的都是可能会有装修需求的人，请尽量引导客户加微信",

  "vector_db_url": "http://127.0.0.1:19530",
  "collection_name" : "home_reno_simplified"
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
global_configs = []
intentions = [
  {
    "intention_id": "I001",
    "intention_name": "微信号码就这些",
    "keywords": [
      "你直接加就行"
    ],
    "semantic": [],
    "llm_description": ["用户报完微信"]
  },
  {
    "intention_id": "I002",
    "intention_name": "直接报微信",
    "keywords": [
      "我说你记"
    ],
    "semantic": ['你给我寄一份吧'],
    "llm_description": ["用户直接说出了自己的微信"]
  },
  {
    "intention_id": "I003",
    "intention_name": "客户拒绝",
    "keywords": [
      "先不用"
    ],
    "semantic":  ["不想吃"],
    "llm_description": ["客户拒绝了当前的要求"]
  },
  {
    "intention_id": "I004",
    "intention_name": "手机号不是微信",
    "keywords": [
        "手机号不是微信号"
    ],
    "semantic": [],
    "llm_description": ["用户表示手机号不是自己的微信"]
  },
  {
    "intention_id": "I005",
    "intention_name": "肯定手机号是微信",
    "keywords": [
        "就这个号"
    ],
    "semantic": [
        "直接发就行"
    ],
    "llm_description": ["用户确认手机号就是自己的微信"]
  },
  {
    "intention_id": "I006",
    "intention_name": "解释开场白",
    "keywords": [
        "你找谁"
    ],
    "semantic": [
      "你好。什么意思"
    ],
    "llm_description": ["用户需要明白为什么打通电话或者为什么在和你对话"]
  },
  {
    "intention_id": "I007",
    "intention_name": "肯定",
    "keywords": [
      "发我信息吧"
    ],
    "semantic": [
      "有这方面需求的"
    ],
    "llm_description": ["用户表示肯定"]
  },
  {
    "intention_id": "I008",
    "intention_name": "没时间",
    "keywords": [
      "没时间"
    ],
    "semantic": [
      "我现在忙着呢"
    ],
    "llm_description": ["用户没有时间"]
  },
  {
    "intention_id": "I009",
    "intention_name": "发资料",
    "keywords": [
        "发个短信"
    ],
    "semantic": [
      "发个资料给我"
    ],
    "llm_description": ["用户要求把资料发过来"]
  },
  {
    "intention_id": "I010",
    "intention_name": "很可爱",
    "keywords": [
      "我很可爱"
    ],
    "semantic": [
      "我好可爱"
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
      "讲重点"
    ],
    "semantic": ["你说重点的"],
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
      "贵姓"
    ],
    "semantic": [
      "你叫什么名字"
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
      "怎么有我手机"
    ],
    "semantic": [
      "你为什么会有我的电话号码"
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
      "能了解到什么"
    ],
    "semantic": [
      "是什么样子的展会"
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
      "直接跟我说"
    ],
    "semantic":  [
      "经理联系我"
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
      "微信发给我"
    ],
    "semantic":  [
      "你加个微信发给我看看"
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
        "match_num": 2
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
              "intention_ids": ["I003", "I008"]
            },
            {
              "branch_id": "IB_wechat2",
              "branch_type": "SURE",
              "branch_name": "肯定",
              "branch_sort":2,
              "intention_ids": ["I007", "I009"]
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
          "node_id": "TN_wechat2",
          "node_name": "加微信肯定",
          "reply_content_info": [{
              "dialog_id":"dialog_TN_wechat2",
              "content":"我已发送添加邀请，您注意通过一下，祝您生活愉快，再见!",
              "variate":{}
          }],
          "action": 1, # 1挂断 2跳转下一主线流程 3跳转指定主线流程
          "master_process_id": None,
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
          "action": 1, # 1挂断 2跳转下一主线流程 3跳转指定主线流程
          "master_process_id": None,
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
            "IB_wechat4": "TN_wechat2"
          },
          "enable_logging": True
        }
      ]
    }
  }
]