from langgraph.constants import END
from langgraph.graph import StateGraph
from pymilvus import MilvusClient, AsyncMilvusClient
from config.config_setup import NodeConfig, AgentConfig, KnowledgeContext, ChatflowDesignContext, GlobalConfigContext
from elements.intention_node import IntentionNode
from elements.reply_node import ReplyNode, ReplyNodeKT, ReplyNodeKGF
from functionals.utils import update_target, next_main_flow
from common.logger import setup_logger

logger = setup_logger('node_initialization', category='node_initialization', console_output=True)

#TODO: factory function to create base node
def create_base_node(
    graph: StateGraph,
    main_flow: dict,
    main_flow_type: str,
    base_node: dict,
    agent_config: AgentConfig,
    knowledge_context: KnowledgeContext,
    global_config_context: GlobalConfigContext,
    chatflow_design_context: ChatflowDesignContext,
    intentions: list,
    milvus_client: MilvusClient | AsyncMilvusClient | None = None,
):
    main_flow_id: str = main_flow.get("main_flow_id", "")
    main_flow_name: str = main_flow.get("main_flow_name", "")
    node_id: str = base_node.get("node_id", "")
    node_name: str = base_node.get("node_name", "")
    reply_content_info: list = base_node.get("reply_content_info", [])
    intention_branches: list = base_node.get("intention_branches", [])
    other_config: dict = base_node.get("other_config", {})
    enable_logging: bool = base_node.get("enable_logging", False)
    """
    Simulates user creating a base node via GUI.
    Adds the node set of one reply node and one intention node to the graph.
    This node can send pre-configured reply to the user first and then tell the intention from the user's next input.
    """
    # Create config (uses global defaults for shared paths via your paths.py or AgentConfig)
    config = NodeConfig(
        main_flow_id=main_flow_id,
        main_flow_name=main_flow_name,
        main_flow_type=main_flow_type,
        node_id=node_id,
        node_name=node_name,
        reply_content_info=reply_content_info,
        intention_branches=intention_branches,
        other_config=other_config,
        enable_logging=enable_logging,
        agent_config=agent_config,
    )

    # Create sub-node names
    reply_node_name = f"{node_id}_reply"
    intention_node_name = f"{node_id}_intention"

    try:
        # Create sub-node instances
        reply_node = ReplyNode(
            config,
            knowledge_context=knowledge_context,
            next_node_name=intention_node_name,
        )
        intention_node = IntentionNode(
            config,
            knowledge_context=knowledge_context,
            global_config_context=global_config_context,
            chatflow_design_context=chatflow_design_context,
            intentions=intentions,
            milvus_client=milvus_client
        )

        # Add to graph
        graph.add_node(reply_node_name, reply_node)
        graph.add_node(intention_node_name, intention_node)

        if reply_content_info: #we stop for user to talk
            graph.add_edge(reply_node_name, END)
        else: #if no reply content se tup, we directly carry on to the intention node
            graph.add_edge(reply_node_name, intention_node_name)

        if enable_logging:
            log_info = (f"普通节点创立 - 主流程ID：{main_flow_id} - 主流程名称：{main_flow_name} - "
                        f"节点ID：{node_id} - 节点名称：{node_name}")
            logger.info("系统消息：%s", log_info)
    except Exception as e:
        logger.error(f"普通节点{node_id}-{node_name}创建失败: {e}")

#TODO: factory function to create transfer node
def create_transfer_node(
    graph: StateGraph,
    main_flow: dict,
    main_flow_type: str,
    transfer_node: dict,
    agent_config: AgentConfig,
    chatflow_design_context: ChatflowDesignContext,
    knowledge_context: KnowledgeContext,
):
    main_flow_id: str = main_flow.get("main_flow_id", "")
    main_flow_name: str = main_flow.get("main_flow_name", "")
    node_id: str = transfer_node.get("node_id", "")
    node_name: str = transfer_node.get("node_name", "")
    reply_content_info: list = transfer_node.get("reply_content_info", [])
    action: int = int(transfer_node.get("action", 0)) # 1-挂断 2-跳转下一主线流程 3-跳转指定主线流程
    transfer_node_id: str|None = transfer_node.get("master_process_id", "")
    other_config: dict = transfer_node.get("other_config", {})
    enable_logging: bool = transfer_node.get("enable_logging", False)
    starting_node_lookup: dict = chatflow_design_context.starting_node_lookup
    sort_lookup: dict = chatflow_design_context.sort_lookup
    """
    Simulates user creating a transfer node via GUI.
    Adds the node set of one reply node and one intention node to the graph.
    It only includes one reply sub-nodes, and gives 2 output: pre-configured reply and designated next-node in state.
    """
    # Create sub-node names
    reply_node_name = f"{node_id}_reply"

    # Identify the next node
    if action not in {1,2,3}:
        e_m = f"转换节点{node_id}-{node_name}执行动作无效"
        logger.error(e_m)
        raise ValueError(e_m)
    if action == 1: # 挂断
        transfer_node_id = "hang_up"
    elif action == 2: # 跳转下一主线流程
        next_main_flow_id = next_main_flow(main_flow_id, sort_lookup)
        if next_main_flow_id: # If there is a next main flow
            transfer_node_id = update_target(next_main_flow_id, starting_node_lookup)
        else:
            logger.info(f"节点{node_id}-{node_name}无下一主线流程。对话进行至此后将挂断。")
            transfer_node_id = "hang_up"
    elif action == 3: # 跳转指定主线流程
        transfer_node_id = update_target(transfer_node_id, starting_node_lookup)

    # Create config (uses global defaults for shared paths via your paths.py or AgentConfig)
    config = NodeConfig(
        main_flow_id=main_flow_id,
        main_flow_name=main_flow_name,
        main_flow_type = main_flow_type,
        node_id=node_id,
        node_name=node_name,
        reply_content_info=reply_content_info,
        transfer_node_id=transfer_node_id,
        other_config=other_config,
        enable_logging=enable_logging,
        agent_config=agent_config
    )

    # Create sub-node instances
    reply_node = ReplyNode(config, knowledge_context=knowledge_context, next_node_name=transfer_node_id)
    
    # Add to graph
    graph.add_node(reply_node_name, reply_node)
    graph.add_edge(reply_node_name, transfer_node_id)

    if enable_logging:
        log_info = (f"转换节点创立 - 主流程ID：{main_flow_id} - 主流程名称：{main_flow_name} "
                    f"- 节点ID：{node_id} - 节点名称：{node_name}")
        logger.info("系统消息：%s", log_info)

#TODO: factory function to create knowledge transfer node
#Knowledge has a separate transfer node creation function because its action is different.
#Its action is similar to knowledge reply node and global config reply node, instead of regular transfer node.
#You can see knowledge transfer node as a mix of regular transfer node and knowledge/global config reply node.
def create_knowledge_transfer_node(
        graph: StateGraph,
        main_flow: dict,
        main_flow_type: str,
        transfer_node: dict,
        agent_config: AgentConfig,
        chatflow_design_context: ChatflowDesignContext,
):
    main_flow_id: str = main_flow.get("main_flow_id", "")
    main_flow_name: str = main_flow.get("main_flow_name", "")
    node_id: str = transfer_node.get("node_id", "")
    node_name: str = transfer_node.get("node_name", "")
    reply_content_info: list = transfer_node.get("reply_content_info", []) #answer_list
    other_config: dict = transfer_node.get("other_config", {})
    enable_logging: bool = transfer_node.get("enable_logging", False)
    reply_node_name = f"{node_id}_reply"

    config = NodeConfig(
        main_flow_id=main_flow_id,
        main_flow_name=main_flow_name,
        main_flow_type=main_flow_type,
        node_id=node_id,
        node_name=node_name,
        reply_content_info=reply_content_info,
        other_config=other_config,
        enable_logging=enable_logging,
        agent_config=agent_config
    )

    reply_node = ReplyNodeKT(config=config,
                             chatflow_design_context=chatflow_design_context,
                             # logic to decide next node:
                             action=transfer_node.get("action", 1),
                             next_=transfer_node.get("master_process_id", None),
                             # master_process_id= transfer_node.get("master_process_id", None)
                             )
    """
    ReplyNodeKT requires next node action. But this node may involve dynamic information from previous
    engagement history in one call, this logic to actually decide next node will still be configured in
    the __call___ of the instance of ReplyNodeKT, instead of here during the creating of the node like
    regular transfer node.    
    """
    graph.add_node(reply_node_name, reply_node)

    if enable_logging:
        log_info = (f"知识库转换节点创立 - 主流程ID：{main_flow_id} - 主流程名称：{main_flow_name} "
                    f"- 节点ID：{node_id} - 节点名称：{node_name}")
        logger.info("系统消息：%s", log_info)

#TODO: factory function to create knowledge reply node
def create_knowledge_reply_node(
        graph: StateGraph,
        knowledge_info: dict,
        agent_config: AgentConfig,
        chatflow_design_context: ChatflowDesignContext,
):
    node_id: str = knowledge_info.get("intention_id", "")
    node_name: str = knowledge_info.get("intention_name", "")
    other_config: dict = knowledge_info.get("other_config", {})

    answer_list: list = knowledge_info.get("answer", [])
    if not answer_list:
        e_m = f"流程创建失败：知识库{node_id}-{node_name}没有设定回答话术"
        logger.error(e_m)
        raise ValueError(e_m)
    enable_logging: bool = knowledge_info.get("enable_logging", False)
    main_flow_id = "knowledge"
    main_flow_name = "知识库"
    reply_node_name = f"{node_id}_reply"

    config = NodeConfig(
        main_flow_id=main_flow_id,
        main_flow_name=main_flow_name,
        main_flow_type="knowledge_reply",
        node_id=node_id,
        node_name=node_name,
        reply_content_info=answer_list,
        other_config=other_config,
        enable_logging=enable_logging,
        agent_config=agent_config
    )

    reply_node = ReplyNodeKGF(config=config, chatflow_design_context=chatflow_design_context)
    """
    ReplyNodeKGF doesn't require next node name as it will decide by itself.
    The transfer logic will only be confirmed when which reply is decided once the chat goes to this node.
    Therefore the next node will only be configures when initializing the actual node, under ReplyNodeKGF.
    Because this node may need to decide go to which main flow, so its initialization input has chatflow_design_context.
    """
    graph.add_node(reply_node_name, reply_node)

    if enable_logging:
        log_info = (f"知识库节点创立 - 主流程ID：{main_flow_id} - 主流程名称：{main_flow_name} "
                    f"- 节点ID：{node_id} - 节点名称：{node_name}")
        logger.info("系统消息：%s", log_info)

#TODO: factory function to create global config reply node
def create_global_reply_node(
        graph: StateGraph,
        global_config: dict,
        agent_config: AgentConfig,
        chatflow_design_context: ChatflowDesignContext,
):
    context_type = int(global_config.get("context_type"))
    if context_type == 1:
        node_id = "no_input"
        node_name = "客户无应答"
    elif context_type == 2:
        node_id = "no_infer_result"
        node_name = "AI未识别"
    else:
        e_m = "全局配置目前仅支持‘1-客户无应答’和‘2-AI未识别’"
        logger.error(e_m)
        raise ValueError(e_m)

    answer_list: list = global_config.get("answer", [])
    enable_logging: bool = global_config.get("enable_logging", False)
    main_flow_id = "global_config"
    main_flow_name = "全局配置"
    reply_node_name = f"{node_id}_reply"

    config = NodeConfig(
        main_flow_id=main_flow_id,
        main_flow_name=main_flow_name,
        main_flow_type="global_config_reply",
        node_id=node_id,
        node_name=node_name,
        reply_content_info=answer_list,
        # global config reply has no other_config
        enable_logging=enable_logging,
        agent_config=agent_config
    )

    reply_node = ReplyNodeKGF(config = config, chatflow_design_context = chatflow_design_context)
    """
    ReplyNodeKGF doesn't require next node name as it will decide by itself.
    The transfer logic will only be confirmed when which reply is decided once the chat goes to this node.
    Therefore the next node will only be configures when initializing the actual node, under ReplyNodeKGF.
    Because this node may need to decide go to which main flow, so its initialization input has chatflow_design_context.
    """
    graph.add_node(reply_node_name, reply_node)

    if enable_logging:
        log_info = (f"全局配置节点创立 - 主流程ID：{main_flow_id} - 主流程名称：{main_flow_name} "
                    f"- 节点ID：{node_id} - 节点名称：{node_name}")
        logger.info("系统消息：%s", log_info)