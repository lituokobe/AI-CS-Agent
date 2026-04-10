from langgraph.constants import END
from langgraph.graph import StateGraph
from config.config_setup import ChatflowDesignContext, KnowledgeContext
from common.logger import setup_logger
from functionals.state import ChatState
from functionals.utils import update_target

logger = setup_logger('edge_initialization', category='edge_initialization', console_output=True)

#TODO: factory function to create router and conditional edges for regular main flows
def create_edges(
        graph: StateGraph,
        main_flow: dict,
        edge_setup: dict,
        chatflow_design_context: ChatflowDesignContext,
        knowledge_context: KnowledgeContext,
):
    main_flow_id: str = main_flow.get("main_flow_id", "")
    main_flow_name: str = main_flow.get("main_flow_name", "")
    node_id: str = edge_setup.get("node_id", "")
    node_name: str = edge_setup.get("node_name", "")
    route_map: dict = edge_setup.get("route_map", {})
    enable_logging: bool = edge_setup.get("enable_logging", False)
    intention_node_id = f"{node_id}_intention"
    starting_node_lookup: dict = chatflow_design_context.starting_node_lookup
    knowledge_multi_round_lookup: dict = knowledge_context.multi_round_lookup

    # Update the target ids in the route map
    updated_route_map = {k: update_target(v, starting_node_lookup) for k, v in route_map.items()}
    local_node_intentions = list(updated_route_map.keys())

    def route_func(state: ChatState) -> str:
        dialog_state = state.get("dialog_state", [])
        if not dialog_state:
            return "hang_up"
        last_dialog_state = dialog_state[-1] if dialog_state else ""

        if not last_dialog_state or last_dialog_state == "hang_up":
            return "hang_up"
        elif last_dialog_state in local_node_intentions: # if the intention is specified by users in the local node configuration
            return updated_route_map[last_dialog_state]
        elif last_dialog_state in knowledge_multi_round_lookup:
            # if the intention is global knowledge with multi-round reply
            # knowledge intention id->knowledge main flow if->first node if of the main flow
            return update_target(knowledge_multi_round_lookup[last_dialog_state], starting_node_lookup)
        else: # if the intention is just a main_flow_id
            return update_target(last_dialog_state, starting_node_lookup)

    graph.add_conditional_edges(intention_node_id, route_func)

    if enable_logging:
        log_info = (f"普通节点条件边创立 - 主流程ID：{main_flow_id} - 主流程名称：{main_flow_name} "
                    f"- 节点ID：{node_id} - 节点名称：{node_name}")
        logger.info("系统消息：%s", log_info)

#TODO: factory function to create router and conditional edges for knowledge
def create_knowledge_edges(
        graph: StateGraph,
        knowledge_info: dict,
        chatflow_design_context: ChatflowDesignContext,
):
    node_id: str = knowledge_info.get("intention_id", "")
    node_name: str = knowledge_info.get("intention_name", "")
    enable_logging: bool = knowledge_info.get("enable_logging", False)
    main_flow_id = "knowledge"
    main_flow_name = "知识库"
    reply_node_name = f"{node_id}_reply"
    starting_node_id: str = chatflow_design_context.starting_node_id

    def route_func(state: ChatState) -> str:
        dialog_state = state.get("dialog_state", [])
        if not dialog_state:
            return f"{starting_node_id}_reply"  # If no history states, just go to the very first node
        else:
            last_state:str = dialog_state[-1]
            if last_state.endswith("_intention"):
                # this means we are not going to hang_up or any _reply node,
                # the global config state is deleted, we are going to wait for the user to talk, so we go to END
                return END # End the flow to wait for user input
            return last_state

    graph.add_conditional_edges(reply_node_name, route_func)

    if enable_logging:
        log_info = (f"知识库回复节点条件边创立 - 主流程ID：{main_flow_id} - 主流程名称：{main_flow_name} "
                    f"- 节点ID：{node_id} - 节点名称：{node_name} - ")
        logger.info("系统消息：%s", log_info)

#TODO: factory function to create router and conditional edges for knowledge transfer nodes
#These are not edges inside the knowledge main flow, it the edges after the knowledge transfer nodes
def create_knowledge_transfer_edges(
        graph: StateGraph,
        main_flow: dict,
        transfer_node: dict,
        chatflow_design_context: ChatflowDesignContext,
):
    main_flow_id: str = main_flow.get("main_flow_id", "")
    main_flow_name: str = main_flow.get("main_flow_name", "")
    node_id: str = transfer_node.get("node_id", "")
    node_name: str = transfer_node.get("node_name", "")
    enable_logging: bool = transfer_node.get("enable_logging", False)

    reply_node_name = f"{node_id}_reply"
    starting_node_id: str = chatflow_design_context.starting_node_id

    def route_func(state: ChatState) -> str:
        dialog_state = state.get("dialog_state", [])
        if not dialog_state:
            return f"{starting_node_id}_reply"  # If no history states, just go to the very first node
        else:
            last_state:str = dialog_state[-1]
            if last_state.endswith("_intention"):
                # this means we are not going to hang_up or any _reply node,
                # the global config state is deleted, we are going to wait for the user to talk, so we go to END
                return END # End the flow to wait for user input
            return last_state

    graph.add_conditional_edges(reply_node_name, route_func)

    if enable_logging:
        log_info = (f"知识库转换节点条件边创立 - 主流程ID：{main_flow_id} - 主流程名称：{main_flow_name} "
                    f"- 节点ID：{node_id} - 节点名称：{node_name} - ")
        logger.info("系统消息：%s", log_info)

#TODO: factory function to create router and conditional edges for global configs
def create_global_edges(
        graph: StateGraph,
        global_config: dict,
        chatflow_design_context: ChatflowDesignContext,
):
    context_type = int(global_config.get("context_type", 0))
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

    enable_logging: bool = global_config.get("enable_logging", False)
    main_flow_id = "global_config"
    main_flow_name = "全局配置"
    reply_node_name = f"{node_id}_reply"
    starting_node_id: str = chatflow_design_context.starting_node_id

    def route_func(state: ChatState) -> str:
        dialog_state = state.get("dialog_state", [])
        if not dialog_state:
            return f"{starting_node_id}_reply"  # If no history states, just go to the very first node
        else:
            last_state:str = dialog_state[-1]
            if last_state.endswith("_intention"):
                # this means we are not going to hang_up or any _reply node,
                # the global config state is deleted, we are going to wait for the user to talk, so we go to END
                return END # End the flow to wait for user input
            return last_state

    graph.add_conditional_edges(reply_node_name, route_func)

    if enable_logging:
        log_info = (f"全局配置节点条件边创立 - 主流程ID：{main_flow_id} - 主流程名称：{main_flow_name} "
                    f"- 节点ID：{node_id} - 节点名称：{node_name}")
        logger.info("系统消息：%s", log_info)