agent_data = {
    "enable_nlp": 0,
    "nlp_threshold": 0.8,
    "intention_priority": 3,
    "use_llm": 1,
    "llm_name": "local_llm",
    "llm_threshold": 0,
    "llm_context_rounds": 10,
    "llm_role_description": "你是淮安车展的客服，需要和报名的用户确认车展细节。",
    "llm_background_info": "你要确认用户是否来参加，并提供车展的时间、地点、交通方式等信息。如果用户有任何疑问，你也需要解答。",
    "vector_db_url": "http://127.0.0.1:19530",
    "collection_name": "tel44e22ddbfa6bdd1a"
}
dialogs = [
    {
        "dialog_id": "3402a805199f25d8",
        "content": "车友您好{{停顿0.5秒}}我是淮安元旦大运河车展的客服，看您是在网上报名了咱们1月1号到3号淮安车展是吧"
    },
    {
        "dialog_id": "ce70cc148a8ace32",
        "content": "车友您好{{停顿0.5秒}}我是淮安元旦大运河车展的客服，看您是在网上报名了咱们1月1号到三号的淮安车展是吧"
    },
    {
        "dialog_id": "acbad8ddf46a7092",
        "content": "好的，给您来电是邀您入场的，这次车展的时间是1月1日-3日，早上九点入场，下午五点闭馆，地址在淮安大运河文化广场(清江浦区漕运东路)，您可以凭车展报名成功的短信入场。{{停顿0.5秒}}现场购车有抽奖、可以享受补贴，更有60+品牌联合参展，还有车模走秀表演，您到时可以带家人朋友一起过来看看"
    },
    {
        "dialog_id": "dd4b86e9be673d1c",
        "content": "是的，您有报过名的，要不然我们这边不会有您的信息"
    },
    {
        "dialog_id": "91f8a00d1a12cdfc",
        "content": "不会耽误您太长时间的，我这边先给您发送一条短信，是咱们淮安车展的电子门票，您到时候如果想来逛逛，出示短信就可以了，如果没时间，不来也没事的"
    },
    {
        "dialog_id": "22241528d6dd1cd7",
        "content": "是这样的，我们将在1月1号-3号举办淮安元旦大运河车展活动，您之前有在我们系统里报过名的，还记得吗"
    },
    {
        "dialog_id": "ea97d3c82567c805",
        "content": "好的，这次车展的时间是1月1日-3日，早上九点入场，下午五点闭馆，地址在淮安大运河文化广场(清江浦区漕运东路)，您到时可以凭车展报名成功的短信入场，如果您没有收到或者误删的活动前还会再次发送一次，不用担心"
    },
    {
        "dialog_id": "a3d37ff946f71c35",
        "content": "好的，没有的话就不打扰您了，再见！"
    },
    {
        "dialog_id": "a2a0dbad3a1ed3f8",
        "content": "好的，那就先不打扰您了，祝您生活愉快，再见"
    },
    {
        "dialog_id": "db8837f2b45b045a",
        "content": "好的，没有的话就不打扰您了，再见！"
    },
    {
        "dialog_id": "6c249d03ffa7b819",
        "content": "没关系，我这边先给您发送一条短信，是咱们淮安车展的电子门票，您之前报名成功的时候应该也收到过，您到时候如果想来逛逛，出示短信就可以了，如果没时间，不来也没事的"
    },
    {
        "dialog_id": "e254e6593060eb84",
        "content": "好的，那就先不打扰您了，祝您生活愉快，再见"
    },
    {
        "dialog_id": "07dd24b22ed1544f",
        "content": "咱们展会是1号-3号开展，一共三天时间，早上9点入场，晚上5点闭馆，就不能进了"
    },
    {
        "dialog_id": "6bf881da507c1147",
        "content": "咱们展会的位置是在淮安大运河文化广场(清江浦区漕运东路)，公交乘坐有轨电车1号线运河广场站下;或乘坐4路;86路;703路到水门桥东下都可以，自驾的话导航搜索“大运河文化广场”即可n"
    },
    {
        "dialog_id": "5cdae3df37604608",
        "content": "这次肯定是可以享受补贴的，但是具体补贴政策得去现场了解，具体是根据品牌车型的不同，补贴也不一样，具体价格还是需要去现场谈的"
    },
    {
        "dialog_id": "2182a2e0088b4f28",
        "content": "咱们本次车展现场品牌有不少呢，具体您可以来现场看看"
    },
    {
        "dialog_id": "a76cb891209280fe",
        "content": "车展的展商一般是当地经销商，优惠幅度很大的"
    },
    {
        "dialog_id": "a4537bf002b41307",
        "content": "外面是有停车位置的，不收费，但是当天车肯定有点多，您可以早点过来"
    },
    {
        "dialog_id": "d2eaad39f794789b",
        "content": "咱们门票是免费的，不收取任何费用，并且一张门票可以同时带五个人入场，您可以带家人朋友一块来看看"
    },
    {
        "dialog_id": "17cae311b01ac6ca",
        "content": "喂，在吗"
    },
    {
        "dialog_id": "41a8bbe5695fa20d",
        "content": "喂，您能听到我说话吗"
    },
    {
        "dialog_id": "21ae9b5dffd1fefc",
        "content": "喂，我这边好像信号不太好，还是听不见您那边的声音，要么我先挂了，之后再联系您，再见"
    },
    {
        "dialog_id": "85b7881fd1088577",
        "content": "不好意思，我没听清，您能再说一遍吗"
    },
    {
        "dialog_id": "32d00d6ddef5ced2",
        "content": "抱歉，还是听不清您说什么，我先挂了，稍后再联系您"
    },
    {
        "dialog_id": "c97297a95b0dc2e5",
        "content": "好的，您还有其他问题吗"
    },
    {
        "dialog_id": "1006ad8cb8632349",
        "content": "好的，您还有其他问题吗"
    },
    {
        "dialog_id": "696b534dd517f757",
        "content": "好的，您还有其他问题吗"
    },
    {
        "dialog_id": "f3fb12ddcfeb5dc4",
        "content": "好的，没有的话就不打扰您了，再见！"
    },
    {
        "dialog_id": "b8bc1ed40c53d707",
        "content": "咱们本次车展现场品牌有不少呢，具体您可以来现场看看"
    }
]
intentions = [
    {
        "intention_id": "60e91dffec4cd7d0",
        "intention_name": "客户表示报过名",
        "keywords": [
            "好像报过",
            "好像有过这回事",
            "^是的"
        ],
        "semantic": [
            "是我报过",
            "对我好像报过",
            "我记得好像报过",
            "我记得这个展",
            "是的我报过名"
        ],
        "llm_description": []
    },
    {
        "intention_id": "a41cdb882e0e3bb7",
        "intention_name": "不咨询",
        "keywords": [
            "没有了",
            "没了"
        ],
        "semantic": [
            "没有问题了",
            "暂时没问题了"
        ],
        "llm_description": []
    },
    {
        "intention_id": "2e35311dfe9f141f",
        "intention_name": "解释开场白",
        "keywords": [
            "做啥",
            "怎么了",
            "打电话干什么",
            "你打电话干什么",
            "你什么事情",
            "你干啥",
            "干嘛的",
            "什么事",
            "啥事",
            "打电话做什么",
            "什么展会",
            "你是谁",
            "听不清",
            "推销什么",
            "你们做什么的",
            "有什么事情",
            "干嘛",
            "搞什么",
            "有什么事",
            "这是哪里",
            "项目",
            "做什么的",
            "干啥",
            "你找谁",
            "干什么",
            "声音太轻",
            "你想做什么",
            "做什么",
            "哪位",
            "你们是做什么的",
            "推销啥",
            "什么项目",
            "什么事情",
            "卖什么",
            "推介什么",
            "你是干什么的",
            "你谁",
            "怎么啦",
            "你有什么事情",
            "什么单位",
            "你是哪里",
            "打电话给我干什么",
            "电话做什么",
            "有什么需要",
            "找我干什么",
            "有啥事",
            "是谁",
            "推介啥",
            "干什么的",
            "你哪位",
            "咋啦",
            "你干什么",
            "什么名字",
            "啥事儿",
            "干啥的",
            "不知道你干什么",
            "不知道你什么意思",
            "你打电话给我为了",
            "你这是哪里",
            "不知道你要干什么"
        ],
        "semantic": [
            "你好。什么意思",
            "没听清你说的什么",
            "什么意思",
            "你说的我没弄明白",
            "你说啥我没听清",
            "你说的什么东西",
            "哪里。什么东西。",
            "你有什么事情吗",
            "再说一遍",
            "没听懂你在说什么",
            "你是做什么的",
            "你讲的什么东西",
            "我没听懂",
            "什么东西",
            "你好，什么意思",
            "你说什么我没听懂",
            "不知道你再说什么",
            "哪里。什么意思。"
        ],
        "llm_description": []
    },
    {
        "intention_id": "84b879aff62e6d07",
        "intention_name": "介绍时间地点表示没问题",
        "keywords": [
            "好的知道了",
            "谢谢我明白了",
            "谢谢我知道了",
            "好的"
        ],
        "semantic": [
            "我知道了谢谢",
            "记住了谢谢",
            "我记住了",
            "我知道了",
            "好的明白了"
        ],
        "llm_description": []
    },
    {
        "intention_id": "09a835a8af0922ec",
        "intention_name": "听到时间后表示没空",
        "keywords": [
            "周末去不了",
            "有安排了",
            "可能去不了",
            "没时间",
            "没空去",
            "太远了不方便",
            "不太方便",
            "应该过不去",
            "没有车去不了",
            "不方便过去"
        ],
        "semantic": [
            "周末去不了",
            "有安排了",
            "可能去不了",
            "应该没时间",
            "可能没空去",
            "太远了不方便",
            "不太方便",
            "应该过不去",
            "没有车去不了",
            "不方便过去"
        ],
        "llm_description": []
    },
    {
        "intention_id": "c3d7fc2e07512533",
        "intention_name": "一般肯定回复",
        "keywords": [
            "嗯行吧",
            "那好吧",
            "那行吧",
            "那你发吧",
            "行吧",
            "嗯好的",
            "好的",
            "没问题",
            "好吧"
        ],
        "semantic": [
            "那你先发过来吧",
            "那你先发吧",
            "那我到时候看情况吧",
            "好吧，可能吧"
        ],
        "llm_description": []
    },
    {
        "intention_id": "47ac2b055b1b1bde",
        "intention_name": "再次表示去不了",
        "keywords": [
            "算了去不了",
            "还是别发了",
            "不用了",
            "别发了",
            "真没时间",
            "不用了谢谢",
            "真没空",
            "真不方便"
        ],
        "semantic": [
            "真没空去",
            "真不方便去",
            "算了别发了",
            "真去不了"
        ],
        "llm_description": []
    },
    {
        "intention_id": "9e15d0444dabe44a",
        "intention_name": "客户表示了解",
        "keywords": [
            "知道了",
            "嗯好的",
            "明白了",
            "嗯知道了",
            "好的",
            "哦知道了",
            "我懂了"
        ],
        "semantic": [
            "我知道了",
            "知道了谢谢",
            "我明白了",
            "了解了谢谢",
            "懂了懂了",
            "大概知道了"
        ],
        "llm_description": []
    },
    {
        "intention_id": "da5314bebfa8ca65",
        "intention_name": "拒绝接听",
        "keywords": [
            "我在忙",
            "没时间",
            "不方便",
            "先挂了",
            "我没空去",
            "别给我打电话了",
            "忙着呢",
            "下次再打吧",
            "算了吧",
            "顾不上",
            "没兴趣",
            "不感兴趣",
            "不想去了"
        ],
        "semantic": [
            "我现在在忙",
            "我现在没空",
            "没时间去",
            "我在开会",
            "我在开车",
            "我在高速上",
            "忙着呢一会再说",
            "别再给我打了",
            "说了去不了",
            "你搞错了"
        ],
        "llm_description": []
    },
    {
        "intention_id": "41554a9a0cec056f",
        "intention_name": "否认报过名",
        "keywords": [
            "我报过吗",
            "我不记得了",
            "有这个事吗",
            "我忘了",
            "没报过吧",
            "我没报过"
        ],
        "semantic": [
            "我报过名吗",
            "我啥时候报过",
            "我什么时候报过",
            "是我报的吗",
            "搞错了吧",
            "我没报过",
            "我忘记了"
        ],
        "llm_description": []
    },
    {
        "intention_id": "e9f432dc2b1cc0aa",
        "intention_name": "肯定",
        "keywords": [
            "挺想去的",
            "挺有意思的",
            "听着还行",
            "应该有时间",
            "我挺想去的",
            "是我报的名",
            "对是我报的",
            "好像是"
        ],
        "semantic": [
            "我还蛮想去的",
            "挺想去的",
            "应该没问题",
            "我觉得能去",
            "是我报的名",
            "对是我报的",
            "好像是吧",
            "好像有这个事"
        ],
        "llm_description": []
    }
]
knowledge = [
    {
        "intention_id": "a512dfe307e8bf18",
        "intention_name": "关于门票",
        "knowledge_type": 2,
        "keywords": [
            "门票免费吗",
            "门票多少钱",
            "门票收费吗",
            "能带家人朋友一起去吗",
            "几个人能进去",
            "和朋友一起",
            "和家人一块",
            "小孩用买票吗",
            "孩子用买票吗"
        ],
        "semantic": [
            "门票多少钱",
            "门票免费吗",
            "门票收费吗",
            "能带家人朋友一起去吗",
            "几个人能进去",
            "和朋友一起",
            "和家人一块",
            "小孩用买票吗",
            "孩子用买票吗"
        ],
        "llm_description": [],
        "answer_type": 1,
        "enable_logging": True,
        "answer": [
            {
                "reply_content_info": [
                    {
                        "dialog_id": "d2eaad39f794789b",
                        "content": "咱们门票是免费的，不收取任何费用，并且一张门票可以同时带五个人入场，您可以带家人朋友一块来看看",
                        "variate": []
                    }
                ],
                "action": 1,
                "next": -2,
                "master_process_id": "c7a69d2701faf541"
            }
        ],
        "other_config": {
            "is_break": 0,
            "break_time": "2.0",
            "wait_time": "3.5",
            "intention_tag": "",
            "no_asr": 0,
            "match_num": 0
        }
    },
    {
        "intention_id": "1aef40085163a44e",
        "intention_name": "关于停车",
        "knowledge_type": 2,
        "keywords": [
            "有停车地方吗",
            "好停车吗",
            "停车收费吗",
            "停车"
        ],
        "semantic": [
            "有停车地方吗",
            "好停车吗",
            "停车收费吗",
            "停车地方大吗"
        ],
        "llm_description": [],
        "answer_type": 1,
        "enable_logging": True,
        "answer": [
            {
                "reply_content_info": [
                    {
                        "dialog_id": "a4537bf002b41307",
                        "content": "外面是有停车位置的，不收费，但是当天车肯定有点多，您可以早点过来",
                        "variate": []
                    }
                ],
                "action": 3,
                "next": 3,
                "master_process_id": "c7a69d2701faf541"
            }
        ],
        "other_config": {
            "is_break": 0,
            "break_time": "2.0",
            "wait_time": "3.5",
            "intention_tag": "",
            "no_asr": 0,
            "match_num": 0
        }
    },
    {
        "intention_id": "3c8957f4d7c8c336",
        "intention_name": "关于展商",
        "knowledge_type": 2,
        "keywords": [
            "展会的车是4S店还是厂家来的",
            "是4S店的吗",
            "是厂家吗",
            "展商",
            "正规吗"
        ],
        "semantic": [
            "展会的车是4S店还是厂家来的",
            "是4S店的吗",
            "是厂家吗",
            "展商正规吗"
        ],
        "llm_description": [],
        "answer_type": 1,
        "enable_logging": True,
        "answer": [
            {
                "reply_content_info": [
                    {
                        "dialog_id": "a76cb891209280fe",
                        "content": "车展的展商一般是当地经销商，优惠幅度很大的",
                        "variate": []
                    }
                ],
                "action": 3,
                "next": 3,
                "master_process_id": "c7a69d2701faf541"
            }
        ],
        "other_config": {
            "is_break": 0,
            "break_time": "2.0",
            "wait_time": "3.5",
            "intention_tag": "",
            "no_asr": 0,
            "match_num": 0
        }
    },
    {
        "intention_id": "d1916498dcd38d84",
        "intention_name": "关于参展品牌",
        "knowledge_type": 2,
        "keywords": [
            "有没有房车",
            "有没有宝马",
            "有没有奥迪",
            "有没有"
        ],
        "semantic": [
            "有没有房车",
            "有没有宝马",
            "有没有奥迪",
            "有没有国产车",
            "新能源车"
        ],
        "llm_description": [],
        "answer_type": 2,
        "enable_logging": True,
        "answer": "a9a241127516e8f0",
        "other_config": {
            "is_break": 0,
            "break_time": "2.0",
            "wait_time": "3.5",
            "intention_tag": "",
            "no_asr": 0,
            "match_num": 0
        }
    },
    {
        "intention_id": "a9376ec2dd615300",
        "intention_name": "关于国补",
        "knowledge_type": 2,
        "keywords": [
            "国补多少钱",
            "享受国补的还可不可以享受首次购车活动",
            "有国补吗",
            "是最低价吗",
            "能便宜吗",
            "能搞价吗",
            "价格还能谈吗",
            "是一口价吗",
            "有多少优惠",
            "能便宜多少",
            "是国补价吗"
        ],
        "semantic": [
            "国补多少钱",
            "享受国补的还可不可以享受首次购车活动",
            "有国补吗",
            "是双重优惠吗",
            "是最低价吗",
            "能便宜吗",
            "能搞价吗",
            "价格还能谈吗",
            "是一口价吗",
            "有多少优惠",
            "能便宜多少",
            "是国补价吗"
        ],
        "llm_description": [],
        "answer_type": 1,
        "enable_logging": True,
        "answer": [
            {
                "reply_content_info": [
                    {
                        "dialog_id": "5cdae3df37604608",
                        "content": "这次肯定是可以享受补贴的，但是具体补贴政策得去现场了解，具体是根据品牌车型的不同，补贴也不一样，具体价格还是需要去现场谈的",
                        "variate": []
                    }
                ],
                "action": 3,
                "next": 3,
                "master_process_id": "c7a69d2701faf541"
            }
        ],
        "other_config": {
            "is_break": 0,
            "break_time": "2.0",
            "wait_time": "3.5",
            "intention_tag": "",
            "no_asr": 0,
            "match_num": 0
        }
    },
    {
        "intention_id": "24d90a4f4211f54c",
        "intention_name": "展会地点",
        "knowledge_type": 2,
        "keywords": [
            "具体地点在哪",
            "在哪",
            "位置在哪",
            "怎么过去",
            "自己开车",
            "自驾",
            "坐公交"
        ],
        "semantic": [
            "具体地点在哪",
            "地点在哪",
            "位置在哪",
            "怎么过去",
            "自己开车",
            "自驾过去",
            "坐公交去",
            "怎么走啊",
            "直接导航"
        ],
        "llm_description": [],
        "answer_type": 1,
        "enable_logging": True,
        "answer": [
            {
                "reply_content_info": [
                    {
                        "dialog_id": "6bf881da507c1147",
                        "content": "咱们展会的位置是在淮安大运河文化广场(清江浦区漕运东路)，公交乘坐有轨电车1号线运河广场站下;或乘坐4路;86路;703路到水门桥东下都可以，自驾的话导航搜索“大运河文化广场”即可n",
                        "variate": []
                    }
                ],
                "action": 3,
                "next": 3,
                "master_process_id": "c7a69d2701faf541"
            }
        ],
        "other_config": {
            "is_break": 0,
            "break_time": "2.0",
            "wait_time": "3.5",
            "intention_tag": "",
            "no_asr": 0,
            "match_num": 0
        }
    },
    {
        "intention_id": "b5887e873a9752a2",
        "intention_name": "展会时间",
        "knowledge_type": 2,
        "keywords": [
            "啥时候来着",
            "啥时候开展",
            "啥时候开展啊",
            "啥时候的事",
            "什么时候",
            "几号来着",
            "几号开展",
            "一共几天啊",
            "几点入场",
            "几点闭馆",
            "啥时候不能进",
            "啥时候能进"
        ],
        "semantic": [
            "啥时候来着",
            "啥时候开展",
            "几号来着",
            "一共几天",
            "啥时候开展啊",
            "啥时候的事",
            "什么时候",
            "几号开展",
            "一共几天啊",
            "几点入场",
            "几点闭馆",
            "啥时候不能进",
            "啥时候能进"
        ],
        "llm_description": [],
        "answer_type": 1,
        "enable_logging": True,
        "answer": [
            {
                "reply_content_info": [
                    {
                        "dialog_id": "07dd24b22ed1544f",
                        "content": "咱们展会是1号-3号开展，一共三天时间，早上9点入场，晚上5点闭馆，就不能进了",
                        "variate": []
                    }
                ],
                "action": 3,
                "next": 3,
                "master_process_id": "c7a69d2701faf541"
            }
        ],
        "other_config": {
            "is_break": 0,
            "break_time": "2.0",
            "wait_time": "3.5",
            "intention_tag": "",
            "no_asr": 0,
            "match_num": 0
        }
    }
]
chatflow_design = [
    {
        "main_flow_id": "636e3ce0e4c12f30",
        "main_flow_name": "开场白",
        "main_flow_content": {
            "starting_node_id": "node-1769670213886-4461",
            "base_nodes": [
                {
                    "node_id": "node-1769670213886-4461",
                    "node_name": "开场白",
                    "reply_content_info": [
                        {
                            "dialog_id": "ce70cc148a8ace32",
                            "content": "车友您好{{停顿0.5秒}}我是淮安元旦大运河车展的客服，看您是在网上报名了咱们1月1号到三号的淮安车展是吧",
                            "variate": []
                        }
                    ],
                    "intention_branches": [
                        {
                            "branch_id": "d7119025b82b4b3f9d6fe3b1aa839ef2",
                            "branch_name": "肯定",
                            "branch_sort": 2,
                            "branch_type": "SURE",
                            "intention_ids": [
                                "60e91dffec4cd7d0"
                            ]
                        },
                        {
                            "branch_id": "f3a3bbedc23545c6a595944833009bdf",
                            "branch_name": "否定",
                            "branch_sort": 3,
                            "branch_type": "DENY",
                            "intention_ids": [
                                "41554a9a0cec056f"
                            ]
                        },
                        {
                            "branch_id": "02175b2ed6524dadaa07f777b0464d3c",
                            "branch_name": "拒绝",
                            "branch_sort": 4,
                            "branch_type": "REJECT",
                            "intention_ids": [
                                "da5314bebfa8ca65"
                            ]
                        },
                        {
                            "branch_id": "83b7bee50d1647129320017f8a6ffc9e",
                            "branch_name": "解释开场白",
                            "branch_sort": 6,
                            "branch_type": "CUSTOMER",
                            "intention_ids": [
                                "2e35311dfe9f141f"
                            ]
                        }
                    ],
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
                },
                {
                    "node_id": "node-1769670635212-2631",
                    "node_name": "否认报过名",
                    "reply_content_info": [
                        {
                            "dialog_id": "dd4b86e9be673d1c",
                            "content": "是的，您有报过名的，要不然我们这边不会有您的信息",
                            "variate": []
                        }
                    ],
                    "intention_branches": [
                        {
                            "branch_id": "f08618b255d442f69f61efbe8b09ca27",
                            "branch_name": "肯定",
                            "branch_sort": 2,
                            "branch_type": "SURE",
                            "intention_ids": [
                                "c3d7fc2e07512533"
                            ]
                        },
                        {
                            "branch_id": "d02f7a6dd5a1454ca810f0b4a7ab44fd",
                            "branch_name": "拒绝",
                            "branch_sort": 4,
                            "branch_type": "REJECT",
                            "intention_ids": [
                                "47ac2b055b1b1bde",
                                "da5314bebfa8ca65"
                            ]
                        }
                    ],
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
                },
                {
                    "node_id": "node-1769671077215-5302",
                    "node_name": "挽留一",
                    "reply_content_info": [
                        {
                            "dialog_id": "91f8a00d1a12cdfc",
                            "content": "不会耽误您太长时间的，我这边先给您发送一条短信，是咱们淮安车展的电子门票，您到时候如果想来逛逛，出示短信就可以了，如果没时间，不来也没事的",
                            "variate": []
                        }
                    ],
                    "intention_branches": [
                        {
                            "branch_id": "aeb27a4b08594319bc4a603c152af646",
                            "branch_name": "肯定",
                            "branch_sort": 2,
                            "branch_type": "SURE",
                            "intention_ids": [
                                "c3d7fc2e07512533",
                                "9e15d0444dabe44a"
                            ]
                        },
                        {
                            "branch_id": "d21f9e1aa404429689ac0baca80343d2",
                            "branch_name": "拒绝",
                            "branch_sort": 4,
                            "branch_type": "REJECT",
                            "intention_ids": [
                                "47ac2b055b1b1bde"
                            ]
                        }
                    ],
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
                },
                {
                    "node_id": "node-1769671291981-1220",
                    "node_name": "解释开场白",
                    "reply_content_info": [
                        {
                            "dialog_id": "22241528d6dd1cd7",
                            "content": "是这样的，我们将在1月1号-3号举办淮安元旦大运河车展活动，您之前有在我们系统里报过名的，还记得吗",
                            "variate": []
                        }
                    ],
                    "intention_branches": [
                        {
                            "branch_id": "db946ec134cf4775bc4cb857dffe7803",
                            "branch_name": "肯定",
                            "branch_sort": 2,
                            "branch_type": "SURE",
                            "intention_ids": [
                                "c3d7fc2e07512533",
                                "e9f432dc2b1cc0aa",
                                "9e15d0444dabe44a"
                            ]
                        },
                        {
                            "branch_id": "a60cde936bb341268e35a5980f3886a3",
                            "branch_name": "否定",
                            "branch_sort": 3,
                            "branch_type": "DENY",
                            "intention_ids": [
                                "41554a9a0cec056f",
                                "09a835a8af0922ec"
                            ]
                        },
                        {
                            "branch_id": "627cc048633448f693aeba081c25559a",
                            "branch_name": "拒绝",
                            "branch_sort": 4,
                            "branch_type": "REJECT",
                            "intention_ids": [
                                "da5314bebfa8ca65"
                            ]
                        }
                    ],
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
                },
                {
                    "node_id": "node-1769671951800-539",
                    "node_name": "挽留成功",
                    "reply_content_info": [
                        {
                            "dialog_id": "ea97d3c82567c805",
                            "content": "好的，这次车展的时间是1月1日-3日，早上九点入场，下午五点闭馆，地址在淮安大运河文化广场(清江浦区漕运东路)，您到时可以凭车展报名成功的短信入场，如果您没有收到或者误删的活动前还会再次发送一次，不用担心",
                            "variate": []
                        }
                    ],
                    "intention_branches": [
                        {
                            "branch_id": "0f47c51d16214363963ae90d7474f751",
                            "branch_name": "肯定",
                            "branch_sort": 2,
                            "branch_type": "SURE",
                            "intention_ids": [
                                "c3d7fc2e07512533",
                                "9e15d0444dabe44a"
                            ]
                        }
                    ],
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
                },
                {
                    "node_id": "node-1769676115732-7309",
                    "node_name": "挂断一",
                    "reply_content_info": [
                        {
                            "dialog_id": "c97297a95b0dc2e5",
                            "content": "好的，您还有其他问题吗",
                            "variate": []
                        }
                    ],
                    "intention_branches": [
                        {
                            "branch_id": "a56b74b5b17c4b2a8ab950b95c561986",
                            "branch_name": "客户表示没有问题",
                            "branch_sort": 6,
                            "branch_type": "CUSTOMER",
                            "intention_ids": [
                                "a41cdb882e0e3bb7"
                            ]
                        }
                    ],
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
                }
            ],
            "transfer_nodes": [
                {
                    "node_id": "node-1769670618240-3332",
                    "node_name": "跳转节点",
                    "reply_content_info": [],
                    "action": 2,
                    "master_process_id": "",
                    "enable_logging": True,
                    "other_config": {
                        "intention_tag": "",
                        "no_asr": -1,
                        "nomatch_knowledge_ids": ""
                    }
                },
                {
                    "node_id": "node-1769672190674-508",
                    "node_name": "挂断",
                    "reply_content_info": [
                        {
                            "dialog_id": "a2a0dbad3a1ed3f8",
                            "content": "好的，那就先不打扰您了，祝您生活愉快，再见",
                            "variate": []
                        }
                    ],
                    "action": 1,
                    "master_process_id": "",
                    "enable_logging": True,
                    "other_config": {
                        "intention_tag": "",
                        "no_asr": -1,
                        "nomatch_knowledge_ids": ""
                    }
                },
                {
                    "node_id": "node-1769672244594-9789",
                    "node_name": "挽留成功挂断",
                    "reply_content_info": [
                        {
                            "dialog_id": "a3d37ff946f71c35",
                            "content": "好的，没有的话就不打扰您了，再见！",
                            "variate": []
                        }
                    ],
                    "action": 1,
                    "master_process_id": "",
                    "enable_logging": True,
                    "other_config": {
                        "intention_tag": "",
                        "no_asr": -1,
                        "nomatch_knowledge_ids": ""
                    }
                }
            ],
            "edge_setups": [
                {
                    "node_id": "node-1769670213886-4461",
                    "node_name": "开场白",
                    "route_map": {
                        "d7119025b82b4b3f9d6fe3b1aa839ef2": "node-1769670618240-3332",
                        "f3a3bbedc23545c6a595944833009bdf": "node-1769670635212-2631",
                        "02175b2ed6524dadaa07f777b0464d3c": "node-1769671077215-5302",
                        "83b7bee50d1647129320017f8a6ffc9e": "node-1769671291981-1220"
                    },
                    "enable_logging": True
                },
                {
                    "node_id": "node-1769670635212-2631",
                    "node_name": "否认报过名",
                    "route_map": {
                        "f08618b255d442f69f61efbe8b09ca27": "node-1769670618240-3332",
                        "d02f7a6dd5a1454ca810f0b4a7ab44fd": "node-1769671077215-5302"
                    },
                    "enable_logging": True
                },
                {
                    "node_id": "node-1769671077215-5302",
                    "node_name": "挽留一",
                    "route_map": {
                        "aeb27a4b08594319bc4a603c152af646": "node-1769671951800-539",
                        "d21f9e1aa404429689ac0baca80343d2": "node-1769672190674-508"
                    },
                    "enable_logging": True
                },
                {
                    "node_id": "node-1769671291981-1220",
                    "node_name": "解释开场白",
                    "route_map": {
                        "db946ec134cf4775bc4cb857dffe7803": "node-1769670618240-3332",
                        "a60cde936bb341268e35a5980f3886a3": "node-1769670635212-2631",
                        "627cc048633448f693aeba081c25559a": "node-1769671077215-5302"
                    },
                    "enable_logging": True
                },
                {
                    "node_id": "node-1769671951800-539",
                    "node_name": "挽留成功",
                    "route_map": {
                        "0f47c51d16214363963ae90d7474f751": "node-1769676115732-7309"
                    },
                    "enable_logging": True
                },
                {
                    "node_id": "node-1769676115732-7309",
                    "node_name": "挂断一",
                    "route_map": {
                        "a56b74b5b17c4b2a8ab950b95c561986": "node-1769672244594-9789"
                    },
                    "enable_logging": True
                }
            ]
        },
        "sort": 0
    },
    {
        "main_flow_id": "1212b2d9aa047290",
        "main_flow_name": "电话邀约",
        "main_flow_content": {
            "starting_node_id": "node-1769670298343-6924",
            "base_nodes": [
                {
                    "node_id": "node-1769670298343-6924",
                    "node_name": "电话邀约",
                    "reply_content_info": [
                        {
                            "dialog_id": "acbad8ddf46a7092",
                            "content": "好的，给您来电是邀您入场的，这次车展的时间是1月1日-3日，早上九点入场，下午五点闭馆，地址在淮安大运河文化广场(清江浦区漕运东路)，您可以凭车展报名成功的短信入场。{{停顿0.5秒}}现场购车有抽奖、可以享受补贴，更有60+品牌联合参展，还有车模走秀表演，您到时可以带家人朋友一起过来看看",
                            "variate": []
                        }
                    ],
                    "intention_branches": [
                        {
                            "branch_id": "fca31b1ae1454aa1818125e3341e988a",
                            "branch_name": "肯定",
                            "branch_sort": 2,
                            "branch_type": "SURE",
                            "intention_ids": [
                                "e9f432dc2b1cc0aa",
                                "c3d7fc2e07512533",
                                "9e15d0444dabe44a",
                                "84b879aff62e6d07"
                            ]
                        },
                        {
                            "branch_id": "814d96d89f28409d88a91f6ea091da06",
                            "branch_name": "否定",
                            "branch_sort": 3,
                            "branch_type": "DENY",
                            "intention_ids": [
                                "09a835a8af0922ec"
                            ]
                        }
                    ],
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
                },
                {
                    "node_id": "node-1769672337287-6243",
                    "node_name": "挽留客户",
                    "reply_content_info": [
                        {
                            "dialog_id": "6c249d03ffa7b819",
                            "content": "没关系，我这边先给您发送一条短信，是咱们淮安车展的电子门票，您之前报名成功的时候应该也收到过，您到时候如果想来逛逛，出示短信就可以了，如果没时间，不来也没事的",
                            "variate": []
                        }
                    ],
                    "intention_branches": [
                        {
                            "branch_id": "de2ce6a7d6c64aa8bed97d9e9be16bf9",
                            "branch_name": "肯定",
                            "branch_sort": 2,
                            "branch_type": "SURE",
                            "intention_ids": [
                                "c3d7fc2e07512533"
                            ]
                        },
                        {
                            "branch_id": "3b91e0f22eaf432daa7b24cb09da05da",
                            "branch_name": "拒绝",
                            "branch_sort": 4,
                            "branch_type": "REJECT",
                            "intention_ids": [
                                "47ac2b055b1b1bde"
                            ]
                        }
                    ],
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
                },
                {
                    "node_id": "node-1769676322658-7447",
                    "node_name": "挂断一",
                    "reply_content_info": [
                        {
                            "dialog_id": "1006ad8cb8632349",
                            "content": "好的，您还有其他问题吗",
                            "variate": []
                        }
                    ],
                    "intention_branches": [
                        {
                            "branch_id": "992bc7be8f2346afaa11c64f9e52f4f5",
                            "branch_name": "肯定",
                            "branch_sort": 2,
                            "branch_type": "SURE",
                            "intention_ids": [
                                "a41cdb882e0e3bb7"
                            ]
                        }
                    ],
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
                }
            ],
            "transfer_nodes": [
                {
                    "node_id": "node-1769672402623-895",
                    "node_name": "挂断",
                    "reply_content_info": [
                        {
                            "dialog_id": "db8837f2b45b045a",
                            "content": "好的，没有的话就不打扰您了，再见！",
                            "variate": []
                        }
                    ],
                    "action": 1,
                    "master_process_id": "",
                    "enable_logging": True,
                    "other_config": {
                        "intention_tag": "",
                        "no_asr": -1,
                        "nomatch_knowledge_ids": ""
                    }
                },
                {
                    "node_id": "node-1769672621557-904",
                    "node_name": "挂断",
                    "reply_content_info": [
                        {
                            "dialog_id": "e254e6593060eb84",
                            "content": "好的，那就先不打扰您了，祝您生活愉快，再见",
                            "variate": []
                        }
                    ],
                    "action": 1,
                    "master_process_id": "",
                    "enable_logging": True,
                    "other_config": {
                        "intention_tag": "",
                        "no_asr": -1,
                        "nomatch_knowledge_ids": ""
                    }
                }
            ],
            "edge_setups": [
                {
                    "node_id": "node-1769670298343-6924",
                    "node_name": "电话邀约",
                    "route_map": {
                        "fca31b1ae1454aa1818125e3341e988a": "node-1769676322658-7447",
                        "814d96d89f28409d88a91f6ea091da06": "node-1769672337287-6243"
                    },
                    "enable_logging": True
                },
                {
                    "node_id": "node-1769672337287-6243",
                    "node_name": "挽留客户",
                    "route_map": {
                        "de2ce6a7d6c64aa8bed97d9e9be16bf9": "node-1769676322658-7447",
                        "3b91e0f22eaf432daa7b24cb09da05da": "node-1769672621557-904"
                    },
                    "enable_logging": True
                },
                {
                    "node_id": "node-1769676322658-7447",
                    "node_name": "挂断一",
                    "route_map": {
                        "992bc7be8f2346afaa11c64f9e52f4f5": "node-1769672402623-895"
                    },
                    "enable_logging": True
                }
            ]
        },
        "sort": 1
    },
    {
        "main_flow_id": "c7a69d2701faf541",
        "main_flow_name": "兜底询问",
        "main_flow_content": {
            "starting_node_id": "node-1769679111696-2687",
            "base_nodes": [
                {
                    "node_id": "node-1769679111696-2687",
                    "node_name": "兜底询问",
                    "reply_content_info": [
                        {
                            "dialog_id": "696b534dd517f757",
                            "content": "好的，您还有其他问题吗",
                            "variate": []
                        }
                    ],
                    "intention_branches": [
                        {
                            "branch_id": "f1b6f9bd0a404ee585e4c70774cf1fbc",
                            "branch_name": "肯定",
                            "branch_sort": 2,
                            "branch_type": "SURE",
                            "intention_ids": [
                                "a41cdb882e0e3bb7"
                            ]
                        }
                    ],
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
                }
            ],
            "transfer_nodes": [
                {
                    "node_id": "node-1769679126833-4961",
                    "node_name": "挂断",
                    "reply_content_info": [
                        {
                            "dialog_id": "f3fb12ddcfeb5dc4",
                            "content": "好的，没有的话就不打扰您了，再见！",
                            "variate": []
                        }
                    ],
                    "action": 1,
                    "master_process_id": "",
                    "enable_logging": True,
                    "other_config": {
                        "intention_tag": "",
                        "no_asr": -1,
                        "nomatch_knowledge_ids": ""
                    }
                }
            ],
            "edge_setups": [
                {
                    "node_id": "node-1769679111696-2687",
                    "node_name": "兜底询问",
                    "route_map": {
                        "f1b6f9bd0a404ee585e4c70774cf1fbc": "node-1769679126833-4961"
                    },
                    "enable_logging": True
                }
            ]
        },
        "sort": 2
    }
]
knowledge_main_flow = [
    {
        "main_flow_id": "a9a241127516e8f0",
        "main_flow_name": "参展品牌",
        "main_flow_content": {
            "starting_node_id": "node-1769735199982-2961",
            "base_nodes": [
                {
                    "node_id": "node-1769735199982-2961",
                    "node_name": "参展品牌",
                    "reply_content_info": [
                        {
                            "dialog_id": "b8bc1ed40c53d707",
                            "content": "咱们本次车展现场品牌有不少呢，具体您可以来现场看看",
                            "variate": []
                        }
                    ],
                    "intention_branches": [
                        {
                            "branch_id": "2dcd70afc7f34312a3a501f8b13a8691",
                            "branch_name": "肯定",
                            "branch_sort": 2,
                            "branch_type": "SURE",
                            "intention_ids": [
                                "9e15d0444dabe44a",
                                "c3d7fc2e07512533"
                            ]
                        }
                    ],
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
                }
            ],
            "transfer_nodes": [
                {
                    "node_id": "node-1769739345598-1284",
                    "node_name": "跳转节点",
                    "reply_content_info": [],
                    "action": 3,
                    "master_process_id": "c7a69d2701faf541",
                    "enable_logging": True,
                    "other_config": {
                        "intention_tag": "",
                        "no_asr": -1,
                        "nomatch_knowledge_ids": ""
                    }
                }
            ],
            "edge_setups": [
                {
                    "node_id": "node-1769735199982-2961",
                    "node_name": "参展品牌",
                    "route_map": {
                        "2dcd70afc7f34312a3a501f8b13a8691": "node-1769739345598-1284"
                    },
                    "enable_logging": True
                }
            ]
        },
        "sort": 0
    }
]
global_configs =[
    {
        "context_type": 2,
        "answer": [
            {
                "reply_content_info": [
                    {
                        "dialog_id": "85b7881fd1088577",
                        "content": "不好意思，我没听清，您能再说一遍吗",
                        "variate": []
                    }
                ],
                "action": 1,
                "next": -1,
                "master_process_id": ""
            },
            {
                "reply_content_info": [
                    {
                        "dialog_id": "32d00d6ddef5ced2",
                        "content": "抱歉，还是听不清您说什么，我先挂了，稍后再联系您",
                        "variate": []
                    }
                ],
                "action": 2,
                "next": -1,
                "master_process_id": ""
            }
        ],
        "intention_tag": 0,
        "status": 1
    },
    {
        "context_type": 1,
        "answer": [
            {
                "reply_content_info": [
                    {
                        "dialog_id": "17cae311b01ac6ca",
                        "content": "喂，在吗",
                        "variate": []
                    }
                ],
                "action": 1,
                "next": -1,
                "master_process_id": ""
            },
            {
                "reply_content_info": [
                    {
                        "dialog_id": "41a8bbe5695fa20d",
                        "content": "喂，您能听到我说话吗",
                        "variate": []
                    }
                ],
                "action": 1,
                "next": -1,
                "master_process_id": ""
            },
            {
                "reply_content_info": [
                    {
                        "dialog_id": "21ae9b5dffd1fefc",
                        "content": "喂，我这边好像信号不太好，还是听不见您那边的声音，要么我先挂了，之后再联系您，再见",
                        "variate": []
                    }
                ],
                "action": 2,
                "next": -1,
                "master_process_id": ""
            }
        ],
        "intention_tag": 0,
        "status": 1
    }
]