import json
import os
from pathlib import Path
from typing import Any, Literal
from pydantic import BaseModel, Field
from functionals.log_utils import logger_chatflow

# Configuration at agent level, the params won't change across nodes
class AgentConfig(BaseModel):
    # Under 设置-模型信息
    enable_nlp: int = Field(..., description="Whether semantic matching is enabled")
    nlp_threshold: float = Field(..., description="Semantic match threshold")
    intention_priority: int = Field(..., description="Priority to infer intentions")
    # Under 设置-大模型匹配
    use_llm: int = Field(..., description="Use LLM for semantic matching")
    llm_name: str = Field(..., description="LLM instance name")
    llm_threshold: int = Field(..., description="The threshold count of user input to use LLM")
    llm_context_rounds: int = Field(..., description="The rounds of chat history for LLM to use")
    llm_role_description: str = Field(..., description="The description of the LLM role")
    llm_background_info: str = Field(..., description="The background information for the LLM role")
    # Vector database
    vector_db_url: str = Field(..., description="Local path for the vector DB")
    collection_name: str = Field(..., description="Vector DB collection data for the whole agent")

# class that holds information related to knowledge base, e.g. data, mapping, matchers.
class KnowledgeContext(BaseModel):
    knowledge: list = Field(..., description="Knowledge data")
    main_flow: list = Field(..., description="Knowledge main flow data")
    main_flow_ids: set = Field(..., description="Knowledge main flow ids")
    infer_name: dict = Field(..., description="Mapping: knowledge ID -> name")
    infer_description: dict = Field(..., description="Mapping: knowledge ID -> name - description")
    type_lookup: dict = Field(..., description="Mapping: knowledge ID -> knowledge type")
    match_lookup: dict = Field(..., description="Mapping: knowledge ID -> knowledge match num")
    multi_round_lookup: dict = Field(..., description="Mapping: knowledge ID -> multi_round_main_flow")
    keyword_matcher: Any = Field(None, description="Knowledge Keyword Matcher instance (if initialized)")
    semantic_matcher: Any = Field(None, description="Knowledge Semantic Matcher instance (if initialized)")

# class that holds information related to chatflow design, e.g. data, mapping.
class ChatflowDesignContext(BaseModel):
    chatflow_design: list = Field(..., description="Chatflow design data")
    starting_node_lookup: dict = Field(..., description="Look-up dict of main_flow_id -> starting_node_id")
    main_flow_lookup: dict = Field(..., description="Look-up dict of starting_node_id -> main_flow_id")
    sort_lookup: dict = Field(..., description="Lookup dict of main_flow_id -> sort")
    mf_node_ids: set = Field(..., description="Node IDs from main_flows only, knowledge is not included.")
    mf_starting_node_ids: set = Field(..., description="Starting node IDs from main_flows only, knowledge is not included.")
    starting_node_id: str = Field(..., description="ID of the very first node of the chatflow")

# class that holds information related to global configurations, e.g. data, status.
class GlobalConfigContext(BaseModel):
    global_configs: list = Field(..., description="Global configuration data")
    no_input: bool = Field(..., description="Whether the reply to no user input is set up")
    no_infer_result: bool = Field(..., description="Whether the reply to on intention identified is set up")

# Configuration at node level
class NodeConfig(BaseModel):
    # Flow level fields
    main_flow_id: str|None = Field(None, description="Main flow ID, unique ID specified by system.")
    main_flow_name: str|None = Field(None, description="Main flow name, created by user.")
    main_flow_type: Literal["regular", "knowledge", "knowledge_reply", "global_config_reply"] | None= Field(None, description="Main flow type")
    # Node-specific fields
    node_id: str|None = Field(None, description="Base node ID, unique ID specified by system.")
    node_name: str|None = Field(None, description="Base node name, created by user.")
    reply_content_info: list|None = Field(None, description="Reply content in the node when the workflow is directed here.")
    intention_branches: list|None = Field(None, description="branches of intentions that includes intention IDs")
    transfer_node_id: str|None = Field(None, description="Action to execute for transfer node")
    other_config: dict|None = Field(None, description="Other config, different for base node, transfer node and knowledge")
    enable_logging: bool = Field(False, description="Enable debug logs")
    # Global config fields at agent level
    agent_config: AgentConfig = Field(..., description="Agent-level configuration")

class ChatFlowConfig(BaseModel):
    agent_config:AgentConfig|None
    knowledge_context:KnowledgeContext|None
    chatflow_design_context:ChatflowDesignContext|None
    global_config_context: GlobalConfigContext|None
    intentions:list[dict|None]

    @classmethod
    def from_files(
            cls,
            agent_data: dict,
            knowledge: list,
            knowledge_main_flow: list,
            chatflow_design: list,
            global_configs_raw: list,
            intentions: list,
    ) -> "ChatFlowConfig":
        # TODO: 1. Prepare agent configuration
        # Initialize agent level data configuration with the loaded agent data
        agent_config = AgentConfig(
            # 设置-模型信息
            enable_nlp=int(agent_data.get("enable_nlp")),
            nlp_threshold=float(agent_data.get("nlp_threshold")),
            intention_priority=int(agent_data.get("intention_priority")),
            # 设置-大模型匹配
            use_llm=int(agent_data.get("use_llm")),
            llm_name=str(agent_data.get("llm_name")),
            llm_threshold=int(agent_data.get("llm_threshold")),
            llm_context_rounds=int(agent_data.get("llm_context_rounds")),
            llm_role_description=str(agent_data.get("llm_role_description")),
            llm_background_info=str(agent_data.get("llm_background_info")),
            # Milvus - vector database; get the url from env first (for docker), if not, get it from agent_data
            vector_db_url=str(
                os.getenv(
                    "MILVUS_URL",
                    agent_data.get("vector_db_url")
                )
            ),
            collection_name=str(agent_data.get("collection_name"))
        )

        # TODO: 2. Use knowledge and knowledge main flows to prepare knowledge context
        knowledge_main_flow_ids = set() # set to store all knowledge main flow ids
        knowledge_infer_name = {} # dict to store knowledge intention_id -> intention_name
        knowledge_infer_description = {} # dict to store knowledge intention_id -> intention_name - description
        knowledge_type_lookup = {} # dict to store knowledge intention_id -> knowledge_type
        knowledge_match_lookup = {} # dict to store knowledge intention_id -> knowledge_match_num
        knowledge_multi_round_lookup = {} # dict to store knowledge intention_id -> multi_round_main_flow

        if knowledge_main_flow:
            for flow in knowledge_main_flow:
                if not isinstance(flow, dict):
                    e_m = "每一个知识库主流程数据应为字典"
                    logger_chatflow.error(e_m)
                    raise TypeError(e_m)
                main_flow_id = flow.get("main_flow_id")
                if main_flow_id:
                    knowledge_main_flow_ids.add(main_flow_id)

        if knowledge:
            for item in knowledge:
                knowledge_infer_name[item["intention_id"]] = item["intention_name"]
                intention_description = " ".join(item["llm_description"]) if item["llm_description"] else "无意图说明"
                knowledge_infer_description[item["intention_id"]] = str(item["intention_name"]) + " - " + intention_description
                knowledge_type_lookup[item["intention_id"]] = item["knowledge_type"]

                match_num = item.get("other_config", {}).get("match_num")
                if not isinstance(match_num, int) or match_num < 1:
                    match_num = 10000
                knowledge_match_lookup[item.get("intention_id")] = match_num

                if item.get("answer_type") == 2:
                    knowledge_multi_round_lookup[item.get("intention_id")] = item.get("answer")
        """
        When use_llm is off or
        llm_threshold > 0 even if use_llm is on (meaning we still use the traditional approaches if user input is below this threshold),
        We initialize the matchers of these traditional approaches: keyword and semantic
        """
        knowledge_context = KnowledgeContext(
            knowledge=knowledge,
            main_flow=knowledge_main_flow,
            main_flow_ids=knowledge_main_flow_ids,
            infer_name=knowledge_infer_name,
            infer_description=knowledge_infer_description,
            type_lookup=knowledge_type_lookup,
            match_lookup=knowledge_match_lookup,
            multi_round_lookup=knowledge_multi_round_lookup,
            keyword_matcher=None,
            semantic_matcher=None
        )

        # TODO: 3. Prepare chatflow context
        # Look-up dict main_flow_id -> starting_node_id
        starting_node_lookup = {}
        # Look-up dict starting_node_id -> main_flow_id
        main_flow_lookup = {}
        # Look-up dict main_flow_id -> sort
        sort_lookup = {}
        # set of all base nodes in mainflows
        mf_node_ids = set()

        for flow in chatflow_design:
            if not isinstance(flow, dict):
                e_m = "每一个主流程数据应为字典"
                logger_chatflow.error(e_m)
                raise TypeError(e_m)
            sort = int(flow.get("sort"))
            main_flow_id = flow.get("main_flow_id")
            main_flow_name = flow.get("main_flow_name", "")
            main_flow_content = flow.get("main_flow_content", {})
            base_nodes = main_flow_content.get("base_nodes")
            starting_node_id = main_flow_content.get("starting_node_id")

            if not isinstance(main_flow_id, str) or not main_flow_id:
                e_m = f"主流程-{main_flow_name}id应为非空字符串"
                logger_chatflow.error(e_m)
                raise TypeError(e_m)
            if not isinstance(starting_node_id, str) or not starting_node_id:
                e_m = f"主流程-{main_flow_name}-{main_flow_id}的初始节点id应为非空字符串"
                logger_chatflow.error(e_m)
                raise TypeError(e_m)
            if not isinstance(base_nodes,
                              list):  # It can be empty list as sometimes there are no base nodes in a main flow
                e_m = f"主流程{main_flow_id}的基础节点设置应为列表"
                logger_chatflow.error(e_m)
                raise TypeError(e_m)

            starting_node_lookup[main_flow_id] = starting_node_id
            main_flow_lookup[starting_node_id] = main_flow_id
            sort_lookup[main_flow_id] = sort
            for base_node in base_nodes:
                node_id = base_node.get("node_id")
                if not isinstance(node_id, str):
                    e_m = f"主流程{main_flow_id}基础节点{node_id}的id应为字符串"
                    logger_chatflow.error(e_m)
                    raise TypeError(e_m)
                mf_node_ids.add(node_id)  # Add all the base node ids from the main flows to mf_node_ids

        # Set of all the starting_node_ids, excluding knowledge
        mf_starting_node_ids = set(starting_node_lookup.values())

        # include the starting node information of knowledge main flow if any
        if knowledge_main_flow:
            for flow in knowledge_main_flow:
                if not isinstance(flow, dict):
                    e_m = "每一个知识库主流程数据应为字典"
                    logger_chatflow.error(e_m)
                    raise TypeError(e_m)
                main_flow_id = flow.get("main_flow_id")
                main_flow_content = flow.get("main_flow_content", {})
                main_flow_name = flow.get("main_flow_name","")
                starting_node_id = main_flow_content.get("starting_node_id")

                if not isinstance(main_flow_id, str) or not main_flow_id:
                    e_m = f"知识库主流程-{main_flow_name}id应为非空字符串"
                    logger_chatflow.error(e_m)
                    raise TypeError(e_m)
                if not isinstance(starting_node_id, str) or not starting_node_id:
                    e_m = f"知识库主流程-{main_flow_name}-{main_flow_id}初始节点id应为非空字符串"
                    logger_chatflow.error(e_m)
                    raise TypeError(e_m)
                starting_node_lookup[main_flow_id] = starting_node_id
                main_flow_lookup[starting_node_id] = main_flow_id
                # Knowledge main flow has no sort or order, no need to consider this information

        # Find the id of starting node of the starting main flow.
        # This node is special because it's triggered first without user's input.
        starting_main_flow_id = min(sort_lookup, key=sort_lookup.get) if sort_lookup else None
        if not isinstance(starting_main_flow_id, str):
            e_m = f"初始主流程ID必须为字符串"
            logger_chatflow.error(e_m)
            raise TypeError(e_m)

        starting_node_id = starting_node_lookup.get(starting_main_flow_id, None)
        if not isinstance(starting_node_id, str):
            e_m = f"项目首个流程的初始节点ID必须为字符串"
            logger_chatflow.error(e_m)
            raise TypeError(e_m)

        # Build the chatflow design context object
        chatflow_design_context = ChatflowDesignContext(
            chatflow_design=chatflow_design,
            starting_node_lookup=starting_node_lookup,
            main_flow_lookup=main_flow_lookup,
            sort_lookup=sort_lookup,
            mf_node_ids=mf_node_ids,
            mf_starting_node_ids=mf_starting_node_ids,
            starting_node_id=starting_node_id
        )

        # TODO 4. Prepare global config context
        # Setup default value
        global_configs = []
        no_input = False
        no_infer_result = False

        # Check global configs
        for global_config in global_configs_raw:
            if not isinstance(global_config, dict):
                e_m = "全局配置必须为字典"
                logger_chatflow.error(e_m)
                raise TypeError(e_m)
            if int(global_config.get("status")) == 1:
                global_configs.append(global_config)
                if int(global_config.get("context_type")) == 1:
                    no_input = True
                if int(global_config.get("context_type")) == 2:
                    no_infer_result = True
                if int(global_config.get("context_type")) not in {1, 2, 3}: # we don't process 3 in this logic
                    e_m = "全局配置语境有误"
                    logger_chatflow.error(e_m)
                    raise TypeError(e_m)

        global_config_context = GlobalConfigContext(
            global_configs=global_configs,
            no_input=no_input,
            no_infer_result=no_infer_result,
        )

        return cls(
            agent_config=agent_config,
            knowledge_context=knowledge_context,
            chatflow_design_context=chatflow_design_context,
            global_config_context=global_config_context,
            intentions=intentions,
        )