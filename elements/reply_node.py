import copy
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from config.config_setup import NodeConfig, ChatflowDesignContext, KnowledgeContext
from data.string_asset import infer_tool_str
from functionals.log_utils import logger_chatflow
from functionals.state import ChatState
from functionals.utils import process_reply, get_last_user_log, get_logs_from_last_user, get_last_user_message, \
    last_message_is_ai, update_target, node_starting_logging, node_ending_logging

#TODO: Class to define regular reply node
#This node will respond the user based on the pre-configured reply
class ReplyNode:
    def __init__(self, config: NodeConfig, knowledge_context: KnowledgeContext, next_node_name:str|None):
        self.config = config
        self.next_node_name = next_node_name

        # Form a list of reply ids for this node.
        self.answer_list_dialog_ids = []
        if self.config.reply_content_info:
            self.answer_list_dialog_ids = [
                asw.get("dialog_id", "") for asw in self.config.reply_content_info
            ]

        # Get all the knowledge main flow ids:
        self.knowledge_main_flow_ids: set = knowledge_context.main_flow_ids

        # Set up "end_call" in metadata
        self.end_call = False
        if self.next_node_name == "hang_up":
            self.end_call = True

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
        messages = state.get("messages", [])
        user_input = get_last_user_message(messages)

        #TODO: Get the last log info
        logs: list = state.get("logs", [])
        previous_log: dict = logs[-1] if logs else {}

        #TODO: Get the last token usage
        token_used = int(previous_log.get("token_used", 0))
        total_token_used = int(previous_log.get("total_token_used", 0))

        #TODO: Decide the reply content, select the first item from reply_content_info
        #Get the last node reply id status. If this node doesn't have a reply status, assign the default answer_list_dialog_ids
        previous_node_reply_id_status = previous_log.get("node_reply_id_status", {})
        node_reply_ids = previous_node_reply_id_status.get(self.config.node_id, self.answer_list_dialog_ids)

        dialog_id, text, variate, reply_content = "", "", {}, ""
        if self.config.reply_content_info:
            next_reply = next(
                (asw for asw in self.config.reply_content_info
                 if asw.get("dialog_id", "") == node_reply_ids[0]),
                {}
            )  # always take the first from node_reply_ids
            dialog_id, text, variate, reply_content = process_reply(next_reply, user_input)

        # Move the node just used to the last
        if len(node_reply_ids) > 1:
            new_node_reply_ids = node_reply_ids[1:] + [node_reply_ids[0]]
        else:
            new_node_reply_ids = copy.deepcopy(node_reply_ids)

        #TODO: Get the last metadata
        metadata: list = state.get("metadata", [])
        previous_metadata:dict = metadata[-1] if metadata else {}

        # Set up reply round and device the previous content in this round
        reply_round: int = previous_metadata.get("reply_round", 0)
        previous_content: list = previous_metadata.get("content", [])
        if not last_message_is_ai(messages):
            # If last round is human, or empty AI message, we add one round.
            # In this round, there should be no previous_content
            previous_content = []
            reply_round += 1

        # Get the last logic
        previous_logic = previous_metadata.get("logic", {})

        # Get the last complete process
        previous_complete_process = previous_logic.get("complete_process", [])

        # Update the complete_process, make it independent of its predecessor
        updated_complete_process = copy.deepcopy(previous_complete_process)

        # Decide whether the main flow is finished by identifying if the node is a transfer node in a main flow
        if self.config.transfer_node_id and self.config.main_flow_type == "regular":  # It's a transfer node
            updated_complete_process.append(self.config.main_flow_id)

        # Setup log info and reply message
        if reply_content:
            current_message = AIMessage(content=reply_content)
            updated_logs = logs + [{
                **previous_log,
                "role": "assistant",
                "content": reply_content,
                "main_flow_id": self.config.main_flow_id,
                "main_flow_name": self.config.main_flow_name,
                "node_id": self.config.node_id,
                "node_name": self.config.node_name,
                "other_config": self.config.other_config or {},
                "node_reply_id_status": {
                    **previous_node_reply_id_status,
                    self.config.node_id: new_node_reply_ids
                }
            }]

            # Create user_logic_title
            last_user_log = get_last_user_log(logs) or {}
            if not last_user_log:
                user_logic_title = {}
            else:
                match_to = last_user_log.get("match_to", "")
                infer_tool = last_user_log.get("infer_tool", "")
                if match_to == "主线流程":
                    if infer_tool == "大模型":
                        user_logic_title = {
                            "匹配到": match_to,
                            "匹配到分支": f"【{last_user_log.get('branch_name','')}】-【{last_user_log.get('intention_name','')}】",
                            "匹配方式": f"【{infer_tool}】",
                            "大模型理解": last_user_log.get('llm_input_summary', '')
                        }
                    elif infer_tool == "关键词":
                        user_logic_title = {
                            "匹配到": match_to,
                            "匹配到分支": f"【{last_user_log.get('branch_name', '')}】-【{last_user_log.get('intention_name', '')}】",
                            "匹配方式": f"【{infer_tool}】",
                            "匹配内容": f"【{last_user_log.get('matching_content')}】",
                            "匹配关键词数量": int(last_user_log.get('matching_score', 0))
                        }
                    elif infer_tool == "问法":
                        user_logic_title = {
                            "匹配到": match_to,
                            "匹配到分支": f"【{last_user_log.get('branch_name', '')}】-【{last_user_log.get('intention_name', '')}】",
                            "匹配方式": f"【{infer_tool}】",
                            "匹配内容": f"【{last_user_log.get('matching_content')}】",
                            "匹配分数": last_user_log.get('matching_score', 0.0)
                        }
                    else:
                        e_m = f"会话{thread_id}，节点{self.config.node_id}-{self.config.node_name}，主线流程匹配方式有误"
                        logger_chatflow.error(e_m)
                        user_logic_title = {
                            "匹配到": match_to,
                            "匹配到分支": f"【{last_user_log.get('branch_name', '')}】-【{last_user_log.get('intention_name', '')}】",
                            "匹配方式": f"【{infer_tool}】",
                        }
                elif match_to == "知识库":
                    if infer_tool == "大模型":
                        user_logic_title = {
                            "匹配到": match_to,
                            "匹配到分支": f"【{last_user_log.get('intention_name', '')}】",
                            "匹配方式": f"【{infer_tool}】",
                            "知识库类型": f"【{last_user_log.get('knowledge_type')}】",
                            "大模型理解": last_user_log.get('llm_input_summary', ''),
                        }
                    elif infer_tool == "关键词":
                        user_logic_title = {
                            "匹配到": match_to,
                            "匹配到分支": f"【{last_user_log.get('intention_name', '')}】",
                            "匹配方式": f"【{infer_tool}】",
                            "知识库类型": f"【{last_user_log.get('knowledge_type')}】",
                            "匹配内容": f"【{last_user_log.get('matching_content')}】",
                            "匹配关键词数量": int(last_user_log.get('matching_score', 0))
                        }
                    elif infer_tool == "问法":
                        user_logic_title = {
                            "匹配到": match_to,
                            "匹配到分支": f"【{last_user_log.get('intention_name', '')}】",
                            "匹配方式": f"【{infer_tool}】",
                            "知识库类型": f"【{last_user_log.get('knowledge_type')}】",
                            "匹配内容": f"【{last_user_log.get('matching_content')}】",
                            "匹配分数": last_user_log.get('matching_score', 0.0)
                        }
                    else:
                        e_m = f"会话{thread_id}，节点{self.config.node_id}-{self.config.node_name}，知识库匹配方式有误"
                        logger_chatflow.error(e_m)
                        user_logic_title = {
                            "匹配到": match_to,
                            "匹配到分支": f"【{last_user_log.get('branch_name', '')}】-【{last_user_log.get('intention_name', '')}】",
                            "匹配方式": f"【{infer_tool}】",
                        }
                elif match_to == "没有意图命中":
                    if infer_tool in set(infer_tool_str):
                        user_logic_title = {
                            "匹配到": match_to,
                            "匹配方式": f"【{infer_tool}】",
                        }
                    else:
                        e_m = f"会话{thread_id}，节点{self.config.node_id}-{self.config.node_name}，没有意图命中匹配方式有误"
                        logger_chatflow.error(e_m)
                        user_logic_title = {
                            "匹配到": match_to,
                            "匹配方式": f"【{infer_tool}】"
                        }
                else:
                    e_m = f"会话{thread_id}，节点{self.config.node_id}-{self.config.node_name}，用户log匹配流程有误"
                    logger_chatflow.error(e_m)
                    user_logic_title = {
                        "匹配到": match_to
                    }

            # Create assistant_logic_title
            if self.config.main_flow_id in self.knowledge_main_flow_ids:
                assistant_logic_title = f"【知识库流程】：{self.config.main_flow_name}、{self.config.node_name}"
            else:
                assistant_logic_title = f"【主线流程】：{self.config.main_flow_name}、{self.config.node_name}"

            updated_metadata = metadata + [{
                **previous_metadata,
                "end_call": self.end_call,
                "reply_round": reply_round,
                "user_input": user_input,
                "token_used": token_used,
                "total_token_used": total_token_used,
                "content" : previous_content +[
                    {
                        "dialog_id": dialog_id,
                        "text": text,
                        "variate": variate,
                        "assistant_logic_title": assistant_logic_title,
                        "other_config": self.config.other_config or {}
                    }
                ],
                "logic":{
                    "user_logic_title":user_logic_title,
                    "complete_process": updated_complete_process,
                    "detail":get_logs_from_last_user(updated_logs)
                },
            }]
        else:
            # When there is no default reply, we only update logs, we don't create any metadata
            current_message = AIMessage(content="")
            updated_logs = logs + [{
                **previous_log,
                "role": "assistant",
                "content": "",
                "main_flow_id": self.config.main_flow_id,
                "main_flow_name": self.config.main_flow_name,
                "node_id": self.config.node_id,
                "node_name": self.config.node_name,
                "other_config": self.config.other_config or {},
                "node_reply_id_status": {
                    **previous_node_reply_id_status,
                    self.config.node_id: new_node_reply_ids
                }
            }]
            # We will not add any extra item to metadata,
            # but need to update complete_process if this is a transfer node of a regular main flow
            updated_metadata = copy.deepcopy(metadata)
            if updated_metadata:
                if "logic" not in updated_metadata[-1]:
                    updated_metadata[-1]["logic"] = {}
                updated_metadata[-1]["logic"]["complete_process"] = updated_complete_process

        # Log information
        if self.config.enable_logging:
            node_ending_logging(self.config, thread_id)
        return {
            "messages": current_message,
            "dialog_state": self.next_node_name,
            "logs": updated_logs,
            "metadata":updated_metadata
        }

#TODO: Class to define reply node for knowledge and global configs
#This node will respond the user based on the pre-configured reply.
#It serves knowledge and global configs.
class ReplyNodeKGF:
    def __init__(self, config: NodeConfig, chatflow_design_context: ChatflowDesignContext):
        self.config = config

        # Set up default value for "end_call" in metadata
        self.end_call = False

        # Get answer list of the global config, including both reply content and relevant actions to next state
        self.answer_list: list = config.reply_content_info or []

        # Form a list of replies for this knowledge/global config.
        # "reply_content_info" only has one dict inside, it's a list for alignment
        self.answer_list_dialog_ids = []
        if self.answer_list:
            try:
                self.answer_list_dialog_ids = [
                    asw.get("reply_content_info", [{}])[0].get("dialog_id", "") for asw in self.answer_list
                ]
            except Exception as e:
                e_m = f"{self.config.node_id}-{self.config.node_name}节点提取回复信息有误: {e}"
                logger_chatflow.error(e_m)
                raise ValueError(e_m)

        # Node information of the whole chatflow design. They will be used to decide next node.
        self.starting_node_id: str = chatflow_design_context.starting_node_id # starting node_id
        self.mf_node_ids: set = chatflow_design_context.mf_node_ids # all the node ids from main flows (excluding knowledge)
        self.mf_starting_node_ids: set = chatflow_design_context.mf_starting_node_ids # all starting node ids from main flows (excluding knowledge)
        self.starting_node_lookup: dict = chatflow_design_context.starting_node_lookup # main flow id -> starting node id

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
        messages = state.get("messages", [])
        user_input = get_last_user_message(messages)

        #TODO: Get the last log info
        logs:list = state.get("logs", [])
        previous_log:dict = logs[-1] if logs else {}

        #TODO: Get the last token usage
        token_used = int(previous_log.get("token_used", 0))
        total_token_used = int(previous_log.get("total_token_used", 0))

        #TODO: Decide the reply content
        #Get the last node reply id status. If this node doesn't have a reply status, assign the default answer_list_dialog_ids
        previous_node_reply_id_status = previous_log.get("node_reply_id_status", {})
        node_reply_ids = previous_node_reply_id_status.get(self.config.node_id, self.answer_list_dialog_ids)

        #Get the reply content, select the first item from reply_content_info
        dialog_id, text, variate, reply_content, next_reply, next_state = "", "", "", "", {}, "hang_up"
        if self.answer_list:
            next_reply = next(
                (asw for asw in self.answer_list
                 if asw.get("reply_content_info", [{}])[0].get("dialog_id", "") == node_reply_ids[0]),
                {}
            ) # always take the first from node_reply_ids
            dialog_id, text, variate, reply_content = process_reply(next_reply.get("reply_content_info", [{}])[0], user_input)

            action = next_reply.get("action", 2)
            # Validate action
            if action not in {1, 2, 3}:  # 1-等待用户回复 2-挂断 3-跳转主流程
                e_m = f"会话{thread_id}，节点{self.config.node_id}-{self.config.node_name}，执行动作无效"
                logger_chatflow.error(e_m) # Only log the error, don't stop the program
                action = 2
        else:
            e_m = f"会话{thread_id}，节点{self.config.node_id}-{self.config.node_name}，没有设定回答话术"
            logger_chatflow.error(e_m) # Only log the error, don't stop the program
            action = 2

        #Move the node just used to the last
        if len(node_reply_ids)>1:
            new_node_reply_ids = node_reply_ids[1:]+[node_reply_ids[0]]
        else:
            new_node_reply_ids = copy.deepcopy(node_reply_ids)

        #TODO: Decide next_state based on the selected reply
        #Get the list of all the states in this chat
        dialog_state = state.get("dialog_state", [])
        if not dialog_state:
            next_state = self.starting_node_id # If no history states, just go to the very first node
        else:
            if action == 1:  # 等待用户回复
                next_state = "pop" # remove the state of this global config, we will get back to the previous node by default
            elif action == 2:  # 挂断
                next_state = "hang_up"
            elif action == 3:  # 指定主线流程
                transfer_node_id = next_reply.get("next")
                if transfer_node_id not in {-1, -2, 3}:  # -1-原主线节点 -2-原主线流程 3-指定主线流程
                    e_m = f"会话{thread_id}，节点{self.config.node_id}-{self.config.node_name}，指定主线流程无效"
                    logger_chatflow.error(e_m)
                    next_state = "hang_up"
                elif transfer_node_id == -1 : # 原主线节点
                    last_mf_node = None
                    for item in reversed(dialog_state):
                        # Update last_intention_node if not already found
                        item_no_suffix = item.removesuffix("_intention")
                        if last_mf_node is None and item_no_suffix in self.mf_node_ids:
                            last_mf_node = item_no_suffix
                            # Early exit
                            break
                    last_mf_node = last_mf_node or self.starting_node_id
                    next_state = f"{last_mf_node}_reply" # go to the base node's reply sub node
                elif transfer_node_id == -2: #原主线流程
                    last_mf_starting_node = None
                    for item in reversed(dialog_state):
                        item_no_suffix = item.removesuffix("_intention")
                        # Update last_main_flow_id if not already found
                        if last_mf_starting_node is None and item_no_suffix in self.mf_starting_node_ids:
                            last_mf_starting_node = item_no_suffix
                            break
                    last_mf_starting_node = last_mf_starting_node or self.starting_node_id
                    next_state = f"{last_mf_starting_node}_reply" # go to the first node of the main flow
                else: # 3- 指定主线流程
                    master_process_id = next_reply.get("master_process_id")
                    next_state = update_target(master_process_id, self.starting_node_lookup) # go to the specified node/main flow
            else:
                next_state = "hang_up"

        if next_state == "hang_up":
            self.end_call = True

        #TODO: Get the last metadata
        metadata:list = state.get("metadata", [])
        previous_metadata:dict = metadata[-1] if metadata else {}

        # Set up reply round and device the previous content in this round
        reply_round:int = previous_metadata.get("reply_round", 0)
        previous_content: list = previous_metadata.get("content", [])
        if not last_message_is_ai(messages):
            # If last round is human, or empty AI message, we add one round.
            # In this round, there should be no previous_content
            previous_content = []
            reply_round += 1

        # Get the last logic, get the complete process (main flow), but we don't touch it here in global config
        previous_logic = previous_metadata.get("logic", {})
        previous_complete_process = previous_logic.get("complete_process", [])
        updated_complete_process = copy.deepcopy(previous_complete_process)

        # Setup log info and reply message
        if reply_content:
            current_message = AIMessage(content=reply_content)
            updated_logs = logs + [{
                **previous_log,
                "role": "assistant",
                "content": reply_content,
                "main_flow_id": self.config.main_flow_id,
                "main_flow_name": self.config.main_flow_name,
                "node_id": self.config.node_id,
                "node_name": self.config.node_name,
                "other_config": self.config.other_config or {},
                "node_reply_id_status":{
                    **previous_node_reply_id_status,
                    self.config.node_id:new_node_reply_ids
                }
            }]

            # Create user_logic_title
            last_user_log = get_last_user_log(logs) or {}
            if not last_user_log:
                user_logic_title = {}
            else:
                match_to = last_user_log.get("match_to", "")
                infer_tool = last_user_log.get("infer_tool", "")
                if match_to == "主线流程":
                    if infer_tool == "大模型":
                        user_logic_title = {
                            "匹配到": match_to,
                            "匹配到分支": f"【{last_user_log.get('branch_name','')}】-【{last_user_log.get('intention_name','')}】",
                            "匹配方式": f"【{infer_tool}】",
                            "大模型理解": last_user_log.get('llm_input_summary', '')
                        }
                    elif infer_tool == "关键词":
                        user_logic_title = {
                            "匹配到": match_to,
                            "匹配到分支": f"【{last_user_log.get('branch_name', '')}】-【{last_user_log.get('intention_name', '')}】",
                            "匹配方式": f"【{infer_tool}】",
                            "匹配内容": f"【{last_user_log.get('matching_content')}】",
                            "匹配关键词数量": int(last_user_log.get('matching_score', 0))
                        }
                    elif infer_tool == "问法":
                        user_logic_title = {
                            "匹配到": match_to,
                            "匹配到分支": f"【{last_user_log.get('branch_name', '')}】-【{last_user_log.get('intention_name', '')}】",
                            "匹配方式": f"【{infer_tool}】",
                            "匹配内容": f"【{last_user_log.get('matching_content')}】",
                            "匹配分数": last_user_log.get('matching_score', 0.0)
                        }
                    else:
                        e_m = f"会话{thread_id}，节点{self.config.node_id}-{self.config.node_name}，主线流程匹配方式有误"
                        logger_chatflow.error(e_m)
                        user_logic_title = {
                            "匹配到": match_to,
                            "匹配到分支": f"【{last_user_log.get('branch_name', '')}】-【{last_user_log.get('intention_name', '')}】",
                            "匹配方式": f"【{infer_tool}】",
                        }
                elif match_to == "知识库":
                    if infer_tool == "大模型":
                        user_logic_title = {
                            "匹配到": match_to,
                            "匹配到分支": f"【{last_user_log.get('intention_name', '')}】",
                            "匹配方式": f"【{infer_tool}】",
                            "知识库类型": f"【{last_user_log.get('knowledge_type')}】",
                            "大模型理解": last_user_log.get('llm_input_summary', ''),
                        }
                    elif infer_tool == "关键词":
                        user_logic_title = {
                            "匹配到": match_to,
                            "匹配到分支": f"【{last_user_log.get('intention_name', '')}】",
                            "匹配方式": f"【{infer_tool}】",
                            "知识库类型": f"【{last_user_log.get('knowledge_type')}】",
                            "匹配内容": f"【{last_user_log.get('matching_content')}】",
                            "匹配关键词数量": int(last_user_log.get('matching_score', 0))
                        }
                    elif infer_tool == "问法":
                        user_logic_title = {
                            "匹配到": match_to,
                            "匹配到分支": f"【{last_user_log.get('intention_name', '')}】",
                            "匹配方式": f"【{infer_tool}】",
                            "知识库类型": f"【{last_user_log.get('knowledge_type')}】",
                            "匹配内容": f"【{last_user_log.get('matching_content')}】",
                            "匹配分数": last_user_log.get('matching_score', 0.0)
                        }
                    else:
                        e_m = f"会话{thread_id}，节点{self.config.node_id}-{self.config.node_name}，知识库匹配方式有误"
                        logger_chatflow.error(e_m)
                        user_logic_title = {
                            "匹配到": match_to,
                            "匹配到分支": f"【{last_user_log.get('branch_name', '')}】-【{last_user_log.get('intention_name', '')}】",
                            "匹配方式": f"【{infer_tool}】",
                        }
                elif match_to == "没有意图命中":
                    if infer_tool in set(infer_tool_str):
                        user_logic_title = {
                            "匹配到": match_to,
                            "匹配方式": f"【{infer_tool}】",
                        }
                    else:
                        e_m = f"会话{thread_id}，节点{self.config.node_id}-{self.config.node_name}，没有意图命中匹配方式有误"
                        logger_chatflow.error(e_m)
                        user_logic_title = {
                            "匹配到": match_to,
                            "匹配方式": f"【{infer_tool}】"
                        }
                else:
                    e_m = f"会话{thread_id}，节点{self.config.node_id}-{self.config.node_name}，用户log匹配流程有误"
                    logger_chatflow.error(e_m)
                    user_logic_title = {
                        "匹配到": match_to
                    }

            # Create assistant_logic_title, self.config.main_flow_name should be 全局配置/知识库
            assistant_logic_title = f"【{self.config.main_flow_name}】：{self.config.node_name}"

            updated_metadata = metadata + [{
                **previous_metadata,
                "end_call": self.end_call,
                "reply_round": reply_round,
                "user_input": user_input,
                "token_used": token_used,
                "total_token_used": total_token_used,
                "content" : previous_content +[
                    {
                        "dialog_id": dialog_id,
                        "text": text,
                        "variate":variate,
                        "assistant_logic_title": assistant_logic_title,
                        "other_config": self.config.other_config or {}
                    }
                ],
                "logic":{
                    "user_logic_title":user_logic_title,
                    "complete_process": updated_complete_process,
                    "detail":get_logs_from_last_user(updated_logs)
                },

            }]
        else:
            # When there is no default reply, we only update logs, we don't create any metadata
            current_message = AIMessage(content="")

            updated_logs = logs + [{
                **previous_log,
                "role": "assistant",
                "content": "",
                "main_flow_id": self.config.main_flow_id,
                "main_flow_name": self.config.main_flow_name,
                "node_id": self.config.node_id,
                "node_name": self.config.node_name,
                "other_config": self.config.other_config or {},
                "node_reply_id_status": {
                    **previous_node_reply_id_status,
                    self.config.node_id: new_node_reply_ids
                }
            }]
            updated_metadata = copy.deepcopy(metadata)
        # Log information
        if self.config.enable_logging:
            node_ending_logging(self.config, thread_id)
        return {
            "messages": current_message,
            "dialog_state": next_state,
            "logs": updated_logs,
            "metadata": updated_metadata
        }

#TODO: Class to define reply node for knowledge transfer node (in knowledge main flow)
#This node will respond the user based on the pre-configured reply.
#It serves knowledge transfer node only.
class ReplyNodeKT:
    def __init__(self,
                 config: NodeConfig,
                 chatflow_design_context: ChatflowDesignContext,
                 # logic to decide next node:
                 action: int,
                 next_:int|str|None,
                 # master_process_id:str|None
                 ):
        self.config = config

        # Set up default value for "end_call" in metadata
        self.end_call = False

        # Get answer list of the global config, including both reply content and relevant actions to next state
        self.reply_content_info: list = config.reply_content_info or []

        # Get the arguments that will decide next node
        self.action = action
        self.next_ = next_
        # self.master_process_id = master_process_id
        if self.action not in {0, 1, 3}:
            e_m = f"知识库转换节点{self.config.node_id}-{self.config.node_name}执行动作无效"
            logger_chatflow.error(e_m)
            raise ValueError(e_m)

        # Form a list of reply ids for this knowledge transfer node.
        self.answer_list_dialog_ids = []
        if self.config.reply_content_info:
            self.answer_list_dialog_ids = [
                asw.get("dialog_id", "") for asw in self.config.reply_content_info
            ]

        # Node information of the whole chatflow design. They will be used to decide next node.
        self.starting_node_id: str = chatflow_design_context.starting_node_id # starting node_id
        self.mf_node_ids: set = chatflow_design_context.mf_node_ids # all the node ids from main flows (excluding knowledge)
        self.mf_starting_node_ids: set = chatflow_design_context.mf_starting_node_ids # all starting node ids from main flows (excluding knowledge)
        self.starting_node_lookup: dict = chatflow_design_context.starting_node_lookup # main flow id -> starting node id

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
        messages = state.get("messages", [])
        user_input = get_last_user_message(messages)

        #TODO: Get the last log info
        logs:list = state.get("logs", [])
        previous_log:dict = logs[-1] if logs else {}

        #TODO: Get the last token usage
        token_used = int(previous_log.get("token_used", 0))
        total_token_used = int(previous_log.get("total_token_used", 0))

        #TODO: Decide the reply content
        #Get the last node reply id status. If this node doesn't have a reply status, assign the default answer_list_dialog_ids
        previous_node_reply_id_status = previous_log.get("node_reply_id_status", {})
        node_reply_ids = previous_node_reply_id_status.get(self.config.node_id, self.answer_list_dialog_ids)

        #Get the reply content, select the first item from reply_content_info
        dialog_id, text, variate, reply_content = "", "", {}, ""
        if self.config.reply_content_info:
            next_reply = next(
                (asw for asw in self.config.reply_content_info
                 if asw.get("dialog_id", "") == node_reply_ids[0]),
                {}
            )  # always take the first from node_reply_ids
            dialog_id, text, variate, reply_content = process_reply(next_reply, user_input)

        # Move the node just used to the last
        if len(node_reply_ids) > 1:
            new_node_reply_ids = node_reply_ids[1:] + [node_reply_ids[0]]
        else:
            new_node_reply_ids = copy.deepcopy(node_reply_ids)

        #TODO: Decide next_state based on input arguments
        #Get the list of all the states in this chat
        dialog_state = state.get("dialog_state", [])

        if self.action == 0:  # 等待用户回复
            next_state = "pop" # remove the state of this global config, we will get back to the previous node by default
        elif self.action == 1:  # 挂断
            next_state = "hang_up"
        else: # self.action == 3 跳转主线流程
            if self.next_ == -1 : # 原主线节点
                last_mf_node = None
                for item in reversed(dialog_state):
                    # Update last_intention_node if not already found
                    item_no_suffix = item.removesuffix("_intention")
                    if last_mf_node is None and item_no_suffix in self.mf_node_ids:
                        last_mf_node = item_no_suffix
                        # Early exit
                        break
                last_mf_node = last_mf_node or self.starting_node_id
                next_state = f"{last_mf_node}_reply" # go to the base node's reply sub node
            elif self.next_ == -2: #原主线流程
                last_mf_starting_node = None
                for item in reversed(dialog_state):
                    item_no_suffix = item.removesuffix("_intention")
                    # Update last_main_flow_id if not already found
                    if last_mf_starting_node is None and item_no_suffix in self.mf_starting_node_ids:
                        last_mf_starting_node = item_no_suffix
                        break
                last_mf_starting_node = last_mf_starting_node or self.starting_node_id
                next_state = f"{last_mf_starting_node}_reply" # go to the first node of the main flow
            elif self.next_ in self.starting_node_lookup: # others - 指定主线流程
                next_state = update_target(self.next_, self.starting_node_lookup)  # go to the specified node/main flow
            else:
                next_state = "hang_up"

        if next_state == "hang_up":
            self.end_call = True

        #TODO: Get the last metadata
        metadata:list = state.get("metadata", [])
        previous_metadata:dict = metadata[-1] if metadata else {}

        # Set up reply round and device the previous content in this round
        reply_round:int = previous_metadata.get("reply_round", 0)
        previous_content: list = previous_metadata.get("content", [])
        if not last_message_is_ai(messages):
            # If last round is human, or empty AI message, we add one round.
            # In this round, there should be no previous_content
            previous_content = []
            reply_round += 1

        # Get the last logic, get the complete process (main flow), but we don't touch it here in global config
        previous_logic = previous_metadata.get("logic", {})
        previous_complete_process = previous_logic.get("complete_process", [])
        updated_complete_process = copy.deepcopy(previous_complete_process)

        # Setup log info and reply message
        if reply_content:
            current_message = AIMessage(content=reply_content)
            updated_logs = logs + [{
                **previous_log,
                "role": "assistant",
                "content": reply_content,
                "main_flow_id": self.config.main_flow_id,
                "main_flow_name": self.config.main_flow_name,
                "node_id": self.config.node_id,
                "node_name": self.config.node_name,
                "other_config": self.config.other_config or {},
                "node_reply_id_status":{
                    **previous_node_reply_id_status,
                    self.config.node_id:new_node_reply_ids
                }
            }]

            # Create user_logic_title
            last_user_log = get_last_user_log(logs) or {}
            if not last_user_log:
                user_logic_title = {}
            else:
                match_to = last_user_log.get("match_to", "")
                infer_tool = last_user_log.get("infer_tool", "")
                if match_to == "主线流程":
                    if infer_tool == "大模型":
                        user_logic_title = {
                            "匹配到": match_to,
                            "匹配到分支": f"【{last_user_log.get('branch_name','')}】-【{last_user_log.get('intention_name','')}】",
                            "匹配方式": f"【{infer_tool}】",
                            "大模型理解": last_user_log.get('llm_input_summary', '')
                        }
                    elif infer_tool == "关键词":
                        user_logic_title = {
                            "匹配到": match_to,
                            "匹配到分支": f"【{last_user_log.get('branch_name', '')}】-【{last_user_log.get('intention_name', '')}】",
                            "匹配方式": f"【{infer_tool}】",
                            "匹配内容": f"【{last_user_log.get('matching_content')}】",
                            "匹配关键词数量": int(last_user_log.get('matching_score', 0))
                        }
                    elif infer_tool == "问法":
                        user_logic_title = {
                            "匹配到": match_to,
                            "匹配到分支": f"【{last_user_log.get('branch_name', '')}】-【{last_user_log.get('intention_name', '')}】",
                            "匹配方式": f"【{infer_tool}】",
                            "匹配内容": f"【{last_user_log.get('matching_content')}】",
                            "匹配分数": last_user_log.get('matching_score', 0.0)
                        }
                    else:
                        e_m = f"会话{thread_id}，节点{self.config.node_id}-{self.config.node_name}，主线流程匹配方式有误"
                        logger_chatflow.error(e_m)
                        user_logic_title = {
                            "匹配到": match_to,
                            "匹配到分支": f"【{last_user_log.get('branch_name', '')}】-【{last_user_log.get('intention_name', '')}】",
                            "匹配方式": f"【{infer_tool}】",
                        }
                elif match_to == "知识库":
                    if infer_tool == "大模型":
                        user_logic_title = {
                            "匹配到": match_to,
                            "匹配到分支": f"【{last_user_log.get('intention_name', '')}】",
                            "匹配方式": f"【{infer_tool}】",
                            "知识库类型": f"【{last_user_log.get('knowledge_type')}】",
                            "大模型理解": last_user_log.get('llm_input_summary', ''),
                        }
                    elif infer_tool == "关键词":
                        user_logic_title = {
                            "匹配到": match_to,
                            "匹配到分支": f"【{last_user_log.get('intention_name', '')}】",
                            "匹配方式": f"【{infer_tool}】",
                            "知识库类型": f"【{last_user_log.get('knowledge_type')}】",
                            "匹配内容": f"【{last_user_log.get('matching_content')}】",
                            "匹配关键词数量": int(last_user_log.get('matching_score', 0))
                        }
                    elif infer_tool == "问法":
                        user_logic_title = {
                            "匹配到": match_to,
                            "匹配到分支": f"【{last_user_log.get('intention_name', '')}】",
                            "匹配方式": f"【{infer_tool}】",
                            "知识库类型": f"【{last_user_log.get('knowledge_type')}】",
                            "匹配内容": f"【{last_user_log.get('matching_content')}】",
                            "匹配分数": last_user_log.get('matching_score', 0.0)
                        }
                    else:
                        e_m = f"会话{thread_id}，节点{self.config.node_id}-{self.config.node_name}，知识库匹配方式有误"
                        logger_chatflow.error(e_m)
                        user_logic_title = {
                            "匹配到": match_to,
                            "匹配到分支": f"【{last_user_log.get('branch_name', '')}】-【{last_user_log.get('intention_name', '')}】",
                            "匹配方式": f"【{infer_tool}】",
                        }
                elif match_to == "没有意图命中":
                    if infer_tool in set(infer_tool_str):
                        user_logic_title = {
                            "匹配到": match_to,
                            "匹配方式": f"【{infer_tool}】"
                        }
                    else:
                        e_m = f"会话{thread_id}，节点{self.config.node_id}-{self.config.node_name}，没有意图命中匹配配方式有误"
                        logger_chatflow.error(e_m)
                        user_logic_title = {
                            "匹配到": match_to,
                            "匹配方式": f"【{infer_tool}】"
                        }
                else:
                    e_m = f"会话{thread_id}，节点{self.config.node_id}-{self.config.node_name}，用户log匹配流程有误"
                    logger_chatflow.error(e_m)
                    user_logic_title = {
                        "匹配到": match_to
                    }

            # Create assistant_logic_title, self.config.main_flow_name should be 全局配置
            assistant_logic_title = f"【知识库流程】：{self.config.main_flow_name}、{self.config.node_name}"

            updated_metadata = metadata + [{
                **previous_metadata,
                "end_call": self.end_call,
                "reply_round": reply_round,
                "user_input": user_input,
                "token_used": token_used,
                "total_token_used": total_token_used,
                "content" : previous_content +[
                    {
                        "dialog_id": dialog_id,
                        "text": text,
                        "variate":variate,
                        "assistant_logic_title": assistant_logic_title,
                        "other_config": self.config.other_config or {}
                    }
                ],
                "logic":{
                    "user_logic_title":user_logic_title,
                    "complete_process": updated_complete_process,
                    "detail":get_logs_from_last_user(updated_logs)
                },
            }]
        else:
            # When there is no default reply, we only update logs, we don't create any metadata
            current_message = AIMessage(content="")

            updated_logs = logs + [{
                **previous_log,
                "role": "assistant",
                "content": "",
                "main_flow_id": self.config.main_flow_id,
                "main_flow_name": self.config.main_flow_name,
                "node_id": self.config.node_id,
                "node_name": self.config.node_name,
                "other_config": self.config.other_config or {},
                "node_reply_id_status": {
                    **previous_node_reply_id_status,
                    self.config.node_id: new_node_reply_ids
                }
            }]
            updated_metadata = copy.deepcopy(metadata)
        # Log information
        if self.config.enable_logging:
            if updated_logs[-1]:
                node_ending_logging(self.config, thread_id)
        return {
            "messages": current_message,
            "dialog_state": next_state,
            "logs": updated_logs,
            "metadata": updated_metadata
        }