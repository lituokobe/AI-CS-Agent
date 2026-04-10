from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.redis import RedisSaver, AsyncRedisSaver
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from pymilvus import AsyncMilvusClient
from config.config_setup import ChatFlowConfig
from elements.edge_initialization import create_edges, create_knowledge_edges, create_global_edges, \
    create_knowledge_transfer_edges
from elements.hang_up_node import hang_up
from elements.node_initialization import create_base_node, create_transfer_node, create_knowledge_reply_node, \
    create_global_reply_node, create_knowledge_transfer_node
from common.logger import setup_logger
from functionals.matchers import KeywordMatcher, SemanticMatcher
from functionals.milvus import initialize_milvus_async
from functionals.state import ChatState

logger = setup_logger('chatflow_builder', category='chatflow_builder', console_output=True)

async def build_chatflow(chatflow_config: ChatFlowConfig, redis_checkpointer: RedisSaver | AsyncRedisSaver | None = None):
    # TODO: Load all the resources
    agent_config = chatflow_config.agent_config
    knowledge_context = chatflow_config.knowledge_context
    chatflow_design_context = chatflow_config.chatflow_design_context
    global_config_context = chatflow_config.global_config_context
    intentions = chatflow_config.intentions
    try:
        model_name = str(agent_config.collection_name).removeprefix("tel")
    except Exception as e:
        logger.error(e)
        model_name = ""

    logger.info(f"模型{model_name}开始准备构建")

    # TODO: Set up matchers for knowledge
    """
    When use_llm is off or 
    llm_threshold > 0 even if use_llm is on (meaning we still use the traditional approaches if user input is below this threshold),
    We initialize the matchers of these traditional approaches: keyword and semantic
    """
    knowledge_keyword_matcher = None
    knowledge_semantic_matcher = None
    milvus_client = AsyncMilvusClient()

    if agent_config.enable_nlp == 1: # Use semantic matching globally
        if agent_config.use_llm !=1 or agent_config.llm_threshold > 0:
            # for intentions from knowledge
            knowledge_keyword_matcher = KeywordMatcher(knowledge_context.knowledge)

            # Initialize Milvus client - Async
            milvus_client: AsyncMilvusClient = await initialize_milvus_async(
                agent_config.vector_db_url,
                agent_config.collection_name,
                intentions,
                knowledge_context.knowledge
            )

            # Initialize knowledge_semantic_matcher
            knowledge_semantic_matcher = SemanticMatcher(
                agent_config.collection_name,
                [item.get("intention_id") for item in knowledge_context.knowledge],
                milvus_client,
            )
    else:
        if agent_config.use_llm != 1 or agent_config.llm_threshold > 0:
            # for intentions from knowledge
            knowledge_keyword_matcher = KeywordMatcher(knowledge_context.knowledge)

    knowledge_context.keyword_matcher=knowledge_keyword_matcher
    knowledge_context.semantic_matcher=knowledge_semantic_matcher

    logger.info(f"模型{model_name}准备完成，开始构建主流程。")

    # TODO: Router function to directly the conversation back to the last node in the state stack before assistant's response
    def route_to_workflow(state: ChatState) -> str:
        dialog_state = state.get("dialog_state", [])
        if not dialog_state:  # At the beginning, send to the first node
            return f"{chatflow_design_context.starting_node_id}_reply"
        elif dialog_state[-1] == "hang_up":
            return END
        else:
            return dialog_state[-1]

    # TODO: Start to build the Graph officially
    graph = StateGraph(ChatState)
    # Create hang_up node. It's better to be created first, other the factory functions later will
    # automatically build edges connected to this node.
    graph.add_node("hang_up", hang_up)

    # TODO: Iterate and build the main flows:
    for main_flow in chatflow_design_context.chatflow_design:
        if not main_flow:
            e_m = "主流程不应为空"
            logger.error(e_m)
            raise TypeError(e_m)

        main_flow_content = main_flow.get("main_flow_content")
        if not main_flow_content:
            e_m = (f"{main_flow.get('main_flow_id')}-{main_flow.get('main_flow_name')}"
                   f"主流程不包含任何节点")
            logger.error(e_m)
            raise TypeError(e_m)

        # Create base nodes:
        base_nodes = main_flow_content.get("base_nodes", [])
        for base_node in base_nodes:
            try:
                create_base_node(
                    graph,
                    main_flow,
                    "regular",
                    base_node,
                    agent_config,
                    knowledge_context,
                    global_config_context,
                    chatflow_design_context,
                    intentions,
                    milvus_client
                )
                logger.info(f"普通节点{base_node.get('node_id', '')}-{base_node.get('node_name', '')}创建成功")
            except Exception as e:
                logger.error(
                    f"普通节点{base_node.get('node_id', '')}-{base_node.get('node_name', '')}"
                    f"创建失败: {e}"
                )

        # Create transfer nodes
        transfer_nodes = main_flow_content.get("transfer_nodes", [])
        for transfer_node in transfer_nodes:
            create_transfer_node(
                graph,
                main_flow,
                "regular",
                transfer_node,
                agent_config,
                chatflow_design_context,
                knowledge_context
            )

        # Create the conditional edges from the base nodes
        edge_setups = main_flow_content.get("edge_setups", [])
        for edge_setup in edge_setups:
            try:
                create_edges(
                    graph,
                    main_flow,
                    edge_setup,
                    chatflow_design_context,
                    knowledge_context
                )
                logger.info(f"普通节点{edge_setup.get('node_id', '')}-{edge_setup.get('node_name', '')}条件边创建成功")
            except Exception as e:
                logger.error(
                    f"普通节点{edge_setup.get('node_id', '')}-{edge_setup.get('node_name', '')}"
                    f"条件边创建失败: {e}"
                )

        logger.info(
            f"模型{model_name}完成构建主流程"
            f"{main_flow.get('main_flow_id')}-{main_flow.get('main_flow_name')}"
        )

    logger.info(f"模型{model_name}主流程构建完毕。")

    # TODO: Create nodes and edges of knowledge
    # Create knowledge reply nodes

    logger.info(f"模型{model_name}准备完成，开始构建知识库。")
    for knowledge_info in knowledge_context.knowledge:
        if knowledge_info.get("answer_type") == 1: #  1-单轮回答 2-多轮回答
            # Only when single round reply is checked, we create knowledge reply node
            create_knowledge_reply_node(
                graph,
                knowledge_info,
                agent_config,
                chatflow_design_context
            )
            create_knowledge_edges(
                graph,
                knowledge_info,
                chatflow_design_context
            )
        logger.info(
            f"模型{model_name}完成构建知识"
            f"{knowledge_info.get('intention_id', '')}-{knowledge_info.get('intention_name', '')}"
        )
    logger.info(f"模型{model_name}知识库构建完毕。")

    # Create knowledge main flows if any
    logger.info(f"模型{model_name}准备完成，开始构建知识库流程。")
    knowledge_main_flow = knowledge_context.main_flow
    if knowledge_main_flow: # Only
        for main_flow in knowledge_main_flow:
            if not main_flow:
                e_m = "知识库流程不应为空"
                logger.error(e_m)
                raise TypeError(e_m)

            main_flow_content = main_flow.get("main_flow_content", {})
            if not main_flow_content:
                e_m = (f"{main_flow.get('main_flow_id')}-{main_flow.get('main_flow_name')}"
                       f"知识库流程不包含任何节点")
                logger.error(e_m)
                raise TypeError(e_m)

            # Create knowledge base nodes:
            base_nodes = main_flow_content.get("base_nodes", [])
            for base_node in base_nodes:
                create_base_node(
                    graph,
                    main_flow,
                    "knowledge",
                    base_node,
                    agent_config,
                    knowledge_context,
                    global_config_context,
                    chatflow_design_context,
                    intentions,
                    milvus_client
                )

            # Create knowledge transfer nodes
            transfer_nodes = main_flow_content.get("transfer_nodes", [])
            for transfer_node in transfer_nodes:
                create_knowledge_transfer_node(
                    graph,
                    main_flow,
                    "knowledge",
                    transfer_node,
                    agent_config,
                    chatflow_design_context
                )

            # Create conditional edges from these transfer nodes
            for transfer_node in transfer_nodes:
                create_knowledge_transfer_edges(
                    graph,
                    main_flow,
                    transfer_node,
                    chatflow_design_context
                )

            # Create the conditional edges from the knowledge base nodes
            edge_setups = main_flow_content.get("edge_setups", [])
            for edge_setup in edge_setups:
                create_edges(
                    graph,
                    main_flow,
                    edge_setup,
                    chatflow_design_context,
                    knowledge_context
                )
        logger.info(
            f"模型{model_name}完成构建知识"
            f"{main_flow.get('main_flow_id')}-{main_flow.get('main_flow_name')}"
        )
    logger.info(f"模型{model_name}知识库流程构建完毕。")

    # TODO: Create nodes and edges of globals
    # Create knowledge reply nodes
    logger.info(f"模型{model_name}准备完成，开始构建全局配置。")
    for global_config in global_config_context.global_configs:
        create_global_reply_node(
            graph,
            global_config,
            agent_config,
            chatflow_design_context
        )
        # Create the conditional edges from knowledge reply nodes
        create_global_edges(
            graph,
            global_config,
            chatflow_design_context
        )
    logger.info(f"模型{model_name}全局配置构建完毕。")

    # TODO: Create the conditional edges from the START node
    graph.add_conditional_edges(START, route_to_workflow)

    logger.info(f"模型{model_name}完成构建。")

    if redis_checkpointer: # In production environment, use Redis as the checkpointer
        return graph.compile(checkpointer=redis_checkpointer), milvus_client

    return graph.compile(checkpointer=MemorySaver()), milvus_client