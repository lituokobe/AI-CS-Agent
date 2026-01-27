import copy
import time
from langchain_core.runnables import RunnableConfig
from pymilvus import MilvusClient
from config.config_setup import NodeConfig, KnowledgeContext, GlobalConfigContext, ChatflowDesignContext
from data.string_asset import infer_tool_str, no_next_main_flow_hang_up_str
from functionals.matchers import KeywordMatcher, SemanticMatcher, LLMInferenceMatcher
from functionals.integrated_matchers import IntegratedSemanticMatcher, IntegratedKeywordsMatcher
from functionals.log_utils import logger_chatflow
from functionals.state import ChatState
from functionals.utils import get_last_user_message, intention_filter, next_main_flow, node_starting_logging, \
    node_ending_logging, get_logs_from_last_user

#TODO: The class of the intention node
class IntentionNode:
    def __init__(self,
                 config: NodeConfig,
                 knowledge_context: KnowledgeContext,
                 global_config_context: GlobalConfigContext,
                 chatflow_design_context: ChatflowDesignContext,
                 intentions: list,
                 milvus_client: MilvusClient | None = None,
                 ):
        self.config = config
        self.knowledge_type_lookup = knowledge_context.type_lookup
        self.knowledge_match_lookup = knowledge_context.match_lookup
        self.global_no_input = global_config_context.no_input
        self.global_no_infer_result = global_config_context.no_infer_result
        self.sort_lookup = chatflow_design_context.sort_lookup
        self.mf_starting_node_ids = chatflow_design_context.mf_starting_node_ids
        self.starting_node_id = chatflow_design_context.starting_node_id
        self.main_flow_lookup = chatflow_design_context.main_flow_lookup
        self.starting_node_lookup = chatflow_design_context.starting_node_lookup

        # Get active intention ids to filter the intention
        # Get active intention id - intention branch id lookup table
        (self.branch_id_lookup,
         self.branch_type_id_lookup, self.branch_id_name_lookup, self.branch_id_type_lookup,
         active_intention_ids) = {}, {}, {}, {}, set()

        # create active_intention_ids
        # create lookup table to look for branch_id, branch_name, and branch_type, with intention_id
        self.sorted_intention_branches = sorted(
            config.intention_branches,
            key=lambda x: x.get("branch_sort", 0)  # Default to 0 if missing
        )
        for branch in self.sorted_intention_branches:
            if branch.get("branch_type"):
                self.branch_type_id_lookup[branch["branch_type"]] = branch.get("branch_id")
            if branch.get("branch_id"):
                self.branch_id_name_lookup[branch["branch_id"]] = branch.get("branch_name")
                self.branch_id_type_lookup[branch["branch_id"]] = branch.get("branch_type")

            intention_ids = branch.get("intention_ids", [])
            if isinstance(intention_ids, list):
                for intention_id in intention_ids:
                    active_intention_ids.add(intention_id) # active_intention_ids is a set, adding duplicated items causes nothing
                    if self.branch_id_lookup.get(intention_id):
                        self.branch_id_lookup[intention_id].append(branch.get("branch_id"))
                    else:
                        self.branch_id_lookup[intention_id] = [branch.get("branch_id")]

        self.default_in_node: bool = "DEFAULT" in self.branch_type_id_lookup
        self.no_reply_in_node: bool = "NO_REPLY" in self.branch_type_id_lookup
        filtered_intentions = intention_filter(intentions, active_intention_ids)

        # Initialize matchers
        nomatch_knowledge_ids = self.config.other_config.get("nomatch_knowledge_ids", [])
        if not isinstance(nomatch_knowledge_ids, list):
            e_m = f"节点{self.config.node_id}-{self.config.node_name}的nomatch_knowledge_ids应为列表"
            logger_chatflow.error(e_m)

        # Initialize matchers
        # Consider the knowledge that is configured not to match in this node
        knowledge_without_nomatch = []
        knowledge_ids_without_nomatch = []
        if nomatch_knowledge_ids:
            for item in knowledge_context.knowledge:
                if item["intention_id"] not in nomatch_knowledge_ids:
                    knowledge_without_nomatch.append(item)
                    knowledge_ids_without_nomatch.append(item["intention_id"])

        # TODO:Always initialize keyword matchers
        #Though it may be redundant in rase cases, but it simplifies the logic.
        self.keyword_matcher = KeywordMatcher(filtered_intentions)
        if knowledge_without_nomatch:
            self.knowledge_keyword_matcher = KeywordMatcher(knowledge_without_nomatch)
        else:
            self.knowledge_keyword_matcher = knowledge_context.keyword_matcher
        # Launch integrated matchers
        self.integrated_keywords_matcher = IntegratedKeywordsMatcher(
            self.config.agent_config.intention_priority,
            self.keyword_matcher,
            self.knowledge_keyword_matcher
        )

        # TODO: Initialize semantic matchers on conditions
        if self.config.agent_config.enable_nlp == 1: # Use semantic matching globally
            self.semantic_matcher = SemanticMatcher(
                config.agent_config.collection_name,
                active_intention_ids, # No need the full intention content, just the ids
                milvus_client
            )
            # for intentions from knowledge
            if knowledge_ids_without_nomatch:
                self.knowledge_semantic_matcher = SemanticMatcher(
                    config.agent_config.collection_name,
                    knowledge_ids_without_nomatch,
                    milvus_client
                )
            else:
                self.knowledge_semantic_matcher = knowledge_context.semantic_matcher

            # Launch integrated matchers
            self.integrated_semantic_matcher = IntegratedSemanticMatcher(
                self.config.agent_config.nlp_threshold,
                self.config.agent_config.intention_priority,
                self.semantic_matcher,
                self.knowledge_semantic_matcher
            )

        # TODO: Initialize LLM matchers on conditions
        if self.config.agent_config.use_llm == 1:
            self.llm_matcher = LLMInferenceMatcher(self.config, # include the "nomatch_knowledge_ids" argument
                                                   filtered_intentions,
                                                   knowledge_context.infer_name,
                                                   knowledge_context.infer_description,
                                                   self.config.agent_config.intention_priority)

    async def __call__(self, state: ChatState, config: RunnableConfig) -> dict:
        #We need to annotate config: RunnableConfig or keep it unannotated.
        #This is more like to tell LangGraph there is a config input argument, instead of type declaration.
        #Annotating it as dict or ANY will lead to error, even if it is a dict.
        #TODO: Get thread id
        #This config is the input argument config that stores thread info, different from self.config
        thread_id = config.get("configurable", {}).get("thread_id", "")
        if not thread_id:
            logger_chatflow.error("当前会话没有thread_id")

        if self.config.enable_logging:
            node_starting_logging(self.config, thread_id)

        #TODO: Get the message and last user message
        messages = state["messages"]
        user_input = get_last_user_message(messages)

        #TODO: Get the last log info
        logs = state.get("logs", [])
        previous_log = logs[-1] if logs else {}
        branch_type_count = copy.deepcopy(previous_log.get("branch_type_count", {}))
        knowledge_match_balance = copy.deepcopy(previous_log.get("knowledge_match_balance", copy.deepcopy(self.knowledge_match_lookup))) # balance knowledge item matches, use deepcopy to isolate each instance
        total_token_used = int(copy.deepcopy(previous_log.get("total_token_used", 0)))

        #TODO: Get the node_branch_status
        previous_node_branch_status = previous_log.get("node_branch_status", {})
        this_node_branches = previous_node_branch_status.get(self.config.node_id, self.branch_id_lookup)

        #TODO: Record the time
        prev_time = time.time()

        #TODO: Identify user intention
        #Set up default outputs
        next_state, branch_id, branch_name, branch_type, knowledge_type = "others", "", "", "", ""
        # === Case 1: Empty input ===
        if not user_input:
            if self.no_reply_in_node: # no reply configuration at node level
                branch_type = "NO_REPLY"
                branch_id = self.branch_type_id_lookup[branch_type]
                branch_name = self.branch_id_name_lookup.get(branch_id)
                branch_type_count[branch_type] = branch_type_count.get(branch_type, 0) + 1
                next_state = branch_id
            elif self.global_no_input: # no reply configuration at globa level
                next_state = "no_input"
            log_info = {
                **previous_log,
                "role": "user",
                "content": user_input,
                "main_flow_id": self.config.main_flow_id,
                "main_flow_name": self.config.main_flow_name,
                "node_id": self.config.node_id,
                "node_name": self.config.node_name,
                "match_to": "没有意图命中", # value can only be from ["没有意图命中", "主线流程", "知识库"]
                "branch_id": branch_id,
                "branch_name": branch_name,
                "branch_type": branch_type,
                "branch_type_count": branch_type_count,
                "intention_id": "",
                "intention_name": "",
                "infer_tool": infer_tool_str[0],
                "llm_input_summary": "",
                "matching_content": "",
                "matching_score": 0.0,
                "knowledge_type": knowledge_type,
                "knowledge_match_balance": knowledge_match_balance,
                "other_config": self.config.other_config or {},
                "token_used": 0,
                "total_token_used": total_token_used,
                "time_cost": 0.0
            }
        # === Case 2: LLM Matching ===
        elif self.config.agent_config.use_llm == 1 and len(user_input) >= self.config.agent_config.llm_threshold:
            # LLM only takes chat history: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}, ...]
            # Keep the last N rounds of chat history specified by the client
            chat_history = messages[-max(1, self.config.agent_config.llm_context_rounds * 2):]
            type_id, type_name, input_summary, infer_type, token_used = await self.llm_matcher.llm_infer(chat_history, user_input)

            if type_name != "其他":
                if infer_type == "意图库":
                    branch_id_list = this_node_branches.get(type_id, [])
                    if branch_id_list:
                        branch_id = branch_id_list[0]
                    else:
                        branch_id = "others"
                    branch_name, branch_type = (self.branch_id_name_lookup.get(branch_id, "其他"),
                                                self.branch_id_type_lookup.get(branch_id, "others"))

                    branch_type_count[branch_type] = branch_type_count.get(branch_type, 0) + 1
                    next_state = branch_id
                    if len(branch_id_list) >= 1:
                        new_branch_id_list = branch_id_list[1:] + [branch_id_list[0]]
                    else:
                        new_branch_id_list = copy.deepcopy(branch_id_list)

                    log_info = {
                        **previous_log,
                        "role": "user",
                        "content": user_input,
                        "main_flow_id": self.config.main_flow_id,
                        "main_flow_name": self.config.main_flow_name,
                        "node_id": self.config.node_id,
                        "node_name": self.config.node_name,
                        "match_to": "主线流程", # value can only be from ["没有意图命中", "主线流程", "知识库"]
                        "branch_id": branch_id,
                        "branch_name": branch_name,
                        "branch_type": branch_type,
                        "branch_type_count": branch_type_count,
                        "node_branch_status": {
                            **previous_node_branch_status,
                            self.config.node_id: {
                                **this_node_branches,
                                type_id:new_branch_id_list
                            }
                        },
                        "intention_id": type_id,
                        "intention_name": type_name,
                        "infer_tool": infer_tool_str[1],
                        "llm_input_summary": input_summary,
                        "matching_content": "",
                        "matching_score": 0.0,
                        "knowledge_type": knowledge_type,
                        "knowledge_match_balance": knowledge_match_balance,
                        "other_config": self.config.other_config or {},
                        "token_used": token_used,
                        "total_token_used": int(total_token_used + token_used),
                        "time_cost": round(time.time() - prev_time, 3)
                    }
                elif infer_type == "知识库":  # If there is no active intentions
                    # Process according to current match balance
                    if not isinstance(knowledge_match_balance.get(type_id), int):
                        e_m = f"会话{thread_id}，节点{self.config.node_id}-{self.config.node_name}，{type_id}不在知识库中"
                        logger_chatflow.error(e_m)
                    # When there IS remaining balance for the knowledge
                    if knowledge_match_balance[type_id] > 0:
                        next_state = type_id  # Navigate to the knowledge reply sub-node
                        knowledge_match_balance[type_id] -= 1
                        knowledge_type = self.knowledge_type_lookup.get(type_id)
                        match_to = "知识库"
                    # When there is NO remaining balance for the knowledge
                    elif self.default_in_node:  # no reply configuration at node level
                        branch_type = "DEFAULT"
                        branch_id = self.branch_type_id_lookup[branch_type]
                        branch_name = self.branch_id_name_lookup.get(branch_id)
                        branch_type_count[branch_type] = branch_type_count.get(branch_type, 0) + 1
                        next_state = branch_id
                        match_to = "没有意图命中"
                    elif self.global_no_infer_result: # no reply configuration at global level
                        next_state = "no_infer_result"
                        match_to = "没有意图命中"
                    else:
                        match_to = "没有意图命中"
                    log_info = {
                        **previous_log,
                        "role": "user",
                        "content": user_input,
                        "main_flow_id": self.config.main_flow_id,
                        "main_flow_name": self.config.main_flow_name,
                        "node_id": self.config.node_id,
                        "node_name": self.config.node_name,
                        "match_to": match_to, # value can only be from ["没有意图命中", "主线流程", "知识库"]
                        "branch_id": branch_id,
                        "branch_name": branch_name,
                        "branch_type": branch_type,
                        "branch_type_count": branch_type_count,
                        "intention_id": type_id,
                        "intention_name": type_name,
                        "infer_tool": infer_tool_str[1],
                        "llm_input_summary": input_summary,
                        "matching_content": "",
                        "matching_score": 0.0,
                        "knowledge_type": knowledge_type,
                        "knowledge_match_balance": knowledge_match_balance,
                        "other_config": self.config.other_config or {},
                        "token_used": token_used,
                        "total_token_used": int(total_token_used + token_used),
                        "time_cost": round(time.time() - prev_time, 3)
                    }
                else:
                    e_m = f"会话{thread_id}，节点{self.config.node_id}-{self.config.node_name}，意图没有来自意图库或知识库"
                    logger_chatflow.error(e_m)
                    log_info = {
                        **previous_log,
                        "role": "user",
                        "content": user_input,
                        "main_flow_id": self.config.main_flow_id,
                        "main_flow_name": self.config.main_flow_name,
                        "node_id": self.config.node_id,
                        "node_name": self.config.node_name,
                        "match_to": "没有意图命中",  # value can only be from ["没有意图命中", "主线流程", "知识库"]
                        "branch_id": branch_id,
                        "branch_name": branch_name,
                        "branch_type": branch_type,
                        "branch_type_count": branch_type_count,
                        "intention_id": type_id,
                        "intention_name": type_name,
                        "infer_tool": infer_tool_str[1],
                        "llm_input_summary": input_summary,
                        "matching_content": "",
                        "matching_score": 0.0,
                        "knowledge_type": knowledge_type,
                        "knowledge_match_balance": knowledge_match_balance,
                        "other_config": self.config.other_config or {},
                        "token_used": token_used,
                        "total_token_used": int(total_token_used + token_used),
                        "time_cost": round(time.time() - prev_time, 3)
                    }
            else: # type_name == "其他"
                if self.default_in_node:  # no reply configuration at node level
                    branch_type = "DEFAULT"
                    branch_id = self.branch_type_id_lookup[branch_type]
                    branch_name = self.branch_id_name_lookup.get(branch_id)
                    branch_type_count[branch_type] = branch_type_count.get(branch_type, 0) + 1
                    next_state = branch_id
                elif self.global_no_infer_result:
                    next_state = "no_infer_result"
                log_info = {
                    **previous_log,
                    "role": "user",
                    "content": user_input,
                    "main_flow_id": self.config.main_flow_id,
                    "main_flow_name": self.config.main_flow_name,
                    "node_id": self.config.node_id,
                    "node_name": self.config.node_name,
                    "match_to": "没有意图命中", # value can only be from ["没有意图命中", "主线流程", "知识库"]
                    "branch_id": branch_id,
                    "branch_name": branch_name,
                    "branch_type": branch_type,
                    "branch_type_count": branch_type_count,
                    "intention_id": "",
                    "intention_name": "",
                    "infer_tool": infer_tool_str[1],
                    "llm_input_summary": input_summary,
                    "matching_content": "",
                    "matching_score": 0.0,
                    "knowledge_type": knowledge_type,
                    "knowledge_match_balance": knowledge_match_balance,
                    "other_config": self.config.other_config or {},
                    "token_used": token_used,
                    "total_token_used": int(total_token_used + token_used),
                    "time_cost": round(time.time() - prev_time, 3)
                }
        else:
            # === Case 3: Keyword Matching ===
            type_id, type_name, keywords, count, infer_type = self.integrated_keywords_matcher.match(user_input)
            if infer_type == "意图库":
                branch_id_list = this_node_branches.get(type_id, [])
                if branch_id_list:
                    branch_id = branch_id_list[0]
                else:
                    branch_id = "others"
                branch_name, branch_type = (self.branch_id_name_lookup.get(branch_id, "其他"),
                                            self.branch_id_type_lookup.get(branch_id, "others"))

                branch_type_count[branch_type] = branch_type_count.get(branch_type, 0) + 1
                
                next_state = branch_id
                
                if len(branch_id_list) >= 1:
                    new_branch_id_list = branch_id_list[1:] + [branch_id_list[0]]
                else:
                    new_branch_id_list = copy.deepcopy(branch_id_list)
                    
                log_info = {
                    **previous_log,
                    "role": "user",
                    "content": user_input,
                    "main_flow_id": self.config.main_flow_id,
                    "main_flow_name": self.config.main_flow_name,
                    "node_id": self.config.node_id,
                    "node_name": self.config.node_name,
                    "match_to": "主线流程", # value can only be from ["没有意图命中", "主线流程", "知识库"]
                    "branch_id": branch_id,
                    "branch_name": branch_name,
                    "branch_type": branch_type,
                    "branch_type_count": branch_type_count,
                    "node_branch_status": {
                        **previous_node_branch_status,
                        self.config.node_id: {
                            **this_node_branches,
                            type_id: new_branch_id_list
                        }
                    },
                    "intention_id": type_id,
                    "intention_name": type_name,
                    "infer_tool": infer_tool_str[2],
                    "llm_input_summary": "",
                    "matching_content": "、".join(keywords),
                    "matching_score": float(count),
                    "knowledge_type": knowledge_type,
                    "knowledge_match_balance": knowledge_match_balance,
                    "other_config": self.config.other_config or {},
                    "token_used": 0,
                    "total_token_used": total_token_used,
                    "time_cost": round(time.time() - prev_time, 3)
                }
            elif infer_type == "知识库":
                # Process according to current match balance
                if not isinstance(knowledge_match_balance.get(type_id), int):
                    e_m = f"会话{thread_id}，节点{self.config.node_id}-{self.config.node_name}，{type_id}不在知识库中"
                    logger_chatflow.error(e_m)
                if knowledge_match_balance[type_id] > 0:
                    next_state = type_id  # Navigate to the knowledge reply sub-node
                    knowledge_match_balance[type_id] -= 1
                    knowledge_type = self.knowledge_type_lookup.get(type_id)
                    match_to = "知识库"
                # When there is NO remaining balance for the knowledge
                elif self.default_in_node:  # no reply configuration at node level
                    branch_type = "DEFAULT"
                    branch_id = self.branch_type_id_lookup[branch_type]
                    branch_name = self.branch_id_name_lookup.get(branch_id)
                    branch_type_count[branch_type] = branch_type_count.get(branch_type, 0) + 1
                    next_state = branch_id
                    match_to = "没有意图命中"
                elif self.global_no_infer_result:  # no reply configuration at global level
                    next_state = "no_infer_result"
                    match_to = "没有意图命中"
                else:
                    match_to = "没有意图命中"

                log_info = {
                    **previous_log,
                    "role": "user",
                    "content": user_input,
                    "main_flow_id": self.config.main_flow_id,
                    "main_flow_name": self.config.main_flow_name,
                    "node_id": self.config.node_id,
                    "node_name": self.config.node_name,
                    "match_to": match_to, # value can only be from ["没有意图命中", "主线流程", "知识库"]
                    "branch_id": branch_id,
                    "branch_name": branch_name,
                    "branch_type": branch_type,
                    "branch_type_count": branch_type_count,
                    "intention_id": type_id,
                    "intention_name": type_name,
                    "infer_tool": infer_tool_str[2],
                    "llm_input_summary": "",
                    "matching_content": "、".join(keywords),
                    "matching_score": float(count),
                    "knowledge_type": knowledge_type,
                    "knowledge_match_balance": knowledge_match_balance,
                    "other_config": self.config.other_config or {},
                    "token_used": 0,
                    "total_token_used": total_token_used,
                    "time_cost": round(time.time() - prev_time, 3)
                }
            # === Case 4: Semantic Matching ===
            elif self.config.agent_config.enable_nlp == 1:
                type_id, type_name, content, cos_score, infer_type = await self.integrated_semantic_matcher.match(user_input)
                if infer_type == "意图库":
                    branch_id_list = this_node_branches.get(type_id, [])
                    if branch_id_list:
                        branch_id = branch_id_list[0]
                    else:
                        branch_id = "others"
                    branch_name, branch_type = (self.branch_id_name_lookup.get(branch_id, "其他"),
                                                self.branch_id_type_lookup.get(branch_id, "others"))

                    branch_type_count[branch_type] = branch_type_count.get(branch_type, 0) + 1
                    next_state = branch_id
                    if len(branch_id_list) >= 1:
                        new_branch_id_list = branch_id_list[1:] + [branch_id_list[0]]
                    else:
                        new_branch_id_list = copy.deepcopy(branch_id_list)
                    
                    log_info = {
                        **previous_log,
                        "role": "user",
                        "content": user_input,
                        "main_flow_id": self.config.main_flow_id,
                        "main_flow_name": self.config.main_flow_name,
                        "node_id": self.config.node_id,
                        "node_name": self.config.node_name,
                        "match_to": "主线流程", # value can only be from ["没有意图命中", "主线流程", "知识库"]
                        "branch_id": branch_id,
                        "branch_name": branch_name,
                        "branch_type": branch_type,
                        "branch_type_count": branch_type_count,
                        "node_branch_status": {
                            **previous_node_branch_status,
                            self.config.node_id: {
                                **this_node_branches,
                                type_id: new_branch_id_list
                            }
                        },
                        "intention_id": type_id,
                        "intention_name": type_name,
                        "infer_tool": infer_tool_str[3],
                        "llm_input_summary": "",
                        "matching_content": content,
                        "matching_score": round(cos_score, 3),
                        "knowledge_type": knowledge_type,
                        "knowledge_match_balance": knowledge_match_balance,
                        "other_config": self.config.other_config or {},
                        "token_used": 0,
                        "total_token_used": total_token_used,
                        "time_cost": round(time.time() - prev_time, 3)
                    }
                elif infer_type == "知识库":
                    # Process according to current match balance
                    if not isinstance(knowledge_match_balance.get(type_id), int):
                        e_m = f"会话{thread_id}，节点{self.config.node_id}-{self.config.node_name}，{type_id}不在知识库中"
                        logger_chatflow.error(e_m)
                        match_to = "知识库"
                    if knowledge_match_balance[type_id] > 0:
                        next_state = type_id  # Navigate to the knowledge reply sub-node
                        knowledge_match_balance[type_id] -= 1
                        knowledge_type = self.knowledge_type_lookup.get(type_id)
                        match_to = "知识库"
                    # When there is NO remaining balance for the knowledge
                    elif self.default_in_node:  # no reply configuration at node level
                        branch_type = "DEFAULT"
                        branch_id = self.branch_type_id_lookup[branch_type]
                        branch_name = self.branch_id_name_lookup.get(branch_id)
                        branch_type_count[branch_type] = branch_type_count.get(branch_type, 0) + 1
                        next_state = branch_id
                        match_to = "没有意图命中"
                    elif self.global_no_infer_result:  # no reply configuration at global level
                        next_state = "no_infer_result"
                        match_to = "没有意图命中"
                    else:
                        match_to = "没有意图命中"
                    log_info = {
                        **previous_log,
                        "role": "user",
                        "content": user_input,
                        "main_flow_id": self.config.main_flow_id,
                        "main_flow_name": self.config.main_flow_name,
                        "node_id": self.config.node_id,
                        "node_name": self.config.node_name,
                        "match_to": match_to, # value can only be from ["没有意图命中", "主线流程", "知识库"]
                        "branch_id": branch_id,
                        "branch_name": branch_name,
                        "branch_type": branch_type,
                        "branch_type_count": branch_type_count,
                        "intention_id": type_id,
                        "intention_name": type_name,
                        "infer_tool": infer_tool_str[3],
                        "llm_input_summary": "",
                        "matching_content": content,
                        "matching_score": round(cos_score, 3),
                        "knowledge_type": knowledge_type,
                        "knowledge_match_balance": knowledge_match_balance,
                        "other_config": self.config.other_config or {},
                        "token_used": 0,
                        "total_token_used": total_token_used,
                        "time_cost": round(time.time() - prev_time, 3)
                    }
                # if it doesn't match anyway
                else:
                    if self.default_in_node:  # no reply configuration at node level
                        branch_type = "DEFAULT"
                        branch_id = self.branch_type_id_lookup[branch_type]
                        branch_name = self.branch_id_name_lookup.get(branch_id)
                        branch_type_count[branch_type] = branch_type_count.get(branch_type, 0) + 1
                        next_state = branch_id
                    elif self.global_no_infer_result:
                        next_state = "no_infer_result"
                    log_info = {
                        **previous_log,
                        "role": "user",
                        "content": user_input,
                        "main_flow_id": self.config.main_flow_id,
                        "main_flow_name": self.config.main_flow_name,
                        "node_id": self.config.node_id,
                        "node_name": self.config.node_name,
                        "match_to": "没有意图命中", # value can only be from ["没有意图命中", "主线流程", "知识库"]
                        "branch_id": branch_id,
                        "branch_name": branch_name,
                        "branch_type": branch_type,
                        "branch_type_count": branch_type_count,
                        "intention_id": "",
                        "intention_name": "",
                        "infer_tool": infer_tool_str[4],
                        "llm_input_summary": "",
                        "matching_content": "",
                        "matching_score": 0.0,
                        "knowledge_type": knowledge_type,
                        "knowledge_match_balance": knowledge_match_balance,
                        "other_config": self.config.other_config or {},
                        "token_used": 0,
                        "total_token_used": total_token_used,
                        "time_cost": round(time.time() - prev_time, 3)
                    }
            # No semantic matching and no match result
            else:
                if self.default_in_node:  # no reply configuration at node level
                    branch_type = "DEFAULT"
                    branch_id = self.branch_type_id_lookup[branch_type]
                    branch_name = self.branch_id_name_lookup.get(branch_id)
                    branch_type_count[branch_type] = branch_type_count.get(branch_type, 0) + 1
                    next_state = branch_id
                elif self.global_no_infer_result:
                    next_state = "no_infer_result"
                log_info = {
                    **previous_log,
                    "role": "user",
                    "content": user_input,
                    "main_flow_id": self.config.main_flow_id,
                    "main_flow_name": self.config.main_flow_name,
                    "node_id": self.config.node_id,
                    "node_name": self.config.node_name,
                    "match_to": "没有意图命中", # value can only be from ["没有意图命中", "主线流程", "知识库"]
                    "branch_id": branch_id,
                    "branch_name": branch_name,
                    "branch_type": branch_type,
                    "branch_type_count": branch_type_count,
                    "intention_id": "",
                    "intention_name": "",
                    "infer_tool": infer_tool_str[5],
                    "llm_input_summary": "",
                    "matching_content": "",
                    "matching_score": 0.0,
                    "knowledge_type": knowledge_type,
                    "knowledge_match_balance": knowledge_match_balance,
                    "other_config": self.config.other_config or {},
                    "token_used": 0,
                    "total_token_used": total_token_used,
                    "time_cost": round(time.time() - prev_time, 3)
                }

        # A correct flow should have a defined next_state at this time
        if next_state == "others":
            e_m = (f"会话{thread_id}，节点{self.config.node_id}-{self.config.node_name}，"
                   f"用户没有输入或意图无法判断。"
                   f"请在本节点或全局配置并设置以应对此种情况。")
            logger_chatflow.error(e_m)
            # Switch to next main flow, until hang_up
            # Get the nearest main_flow_id that is not from knowledge,
            # It can be current main_flow_id or last main_flow_id if we are in a knowledge intention node
            current_starting_node_id = self.starting_node_id
            for st in reversed(state.get("dialog_state", [])):
                st_nosuffix = st.removesuffix("_intention")
                if st_nosuffix in self.mf_starting_node_ids:
                    current_starting_node_id = st_nosuffix
                    break
            current_main_flow_id = self.main_flow_lookup.get(current_starting_node_id, "")
            next_main_flow_id = next_main_flow(current_main_flow_id, self.sort_lookup)
            if not next_main_flow_id:  # If there is a next main flow
                logger_chatflow.info(f"会话{thread_id}，节点{self.config.node_id}-{self.config.node_name}，无下一主线流程。对话进行至此后将挂断。")
            next_state = next_main_flow_id or "hang_up"

        updated_logs = logs + [log_info]

        #TODO: update metadata
        #Sometimes intention node can also lead to hang_up. So we still need to update metadata in this scenario
        updated_metadata: list = state.get("metadata", [])
        if next_state == "hang_up":
            previous_metadata: dict = updated_metadata[-1] if updated_metadata else {}
            previous_logic: dict = previous_metadata.get("logic", {})
            previous_reply_round:int = previous_metadata.get("reply_round", 0)
            updated_metadata.append({
                **previous_metadata,
                "end_call":True,
                "user_input":user_input,
                "reply_round":previous_reply_round+1,
                "content":[{
                        "dialog_id": "hang_up",
                        "text": no_next_main_flow_hang_up_str,
                        "variate": {},
                        "assistant_logic_title": f"已到最后一个流程：{self.config.main_flow_name}，通话将挂断",
                        "other_config": {}
                    }],
                "logic":{
                    **previous_logic,
                    "user_logic_title": {
                        "匹配到": log_info.get("match_to", ""),
                        "匹配方式": f"【{log_info.get('infer_tool', '')}】"
                    },
                    "detail": get_logs_from_last_user(updated_logs)
                },
            })

        if self.config.enable_logging:
            # logger_chatflow.info(
            #     "本节点最新log：%s",
            #     "; ".join(
            #         f"{k}:{(v[:12] + '...' if k == 'content' and isinstance(v, str) and len(v) > 12 else v)}"
            #         for k, v in updated_logs[-1].items()
            #     )
            # )
            node_ending_logging(self.config, thread_id, updated_logs[-1].get("time_cost", 0.0) if updated_logs else 0.0)

        return {
            "dialog_state": next_state,
            "logs":updated_logs,
            "metadata": state["metadata"]
        }