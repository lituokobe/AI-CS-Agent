import copy
from config.config_setup import NodeConfig
from functionals.log_utils import logger_chatflow

# Retrieve the last message from the user in the stack of messages
def get_last_user_message(messages: list) -> str:
    for msg in reversed(messages):
        if msg.__class__.__name__ == "HumanMessage":
            return msg.content
    return ""

# Identify if the last message is from AI with real content
def last_message_is_ai(messages: list) -> bool:
    if messages:
        last_message = messages[-1]
        if last_message.__class__.__name__ == "AIMessage" and last_message.content:
            return True
    return False

# Filter the keywords/semantic dictionary to only include entries with selected ids.
def str_dict_select(str_dict: dict, ids: list[str] | None) -> dict:
    """
    Filter the keywords/semantic dictionary to only include entries with selected ids.
    Args:
        str_dict: Original dict in format {"001": {"label": [...]}, ...}
        ids: List of selected ids (e.g., ["001", "003"])

    Returns:
        Filtered dict containing only the specified str_dicts.
        If there is no ids input, the filtered dict is empty.

    Raises:
        ValueError: If any id is not found in the dict.
    """
    filtered = {}
    missing = []
    if ids:
        for _id in ids:
            if _id in str_dict:
                filtered[_id] = str_dict[_id]
            else:
                missing.append(_id)
        if missing:
            e_m = f"以下意图id不存在：{missing}"
            logger_chatflow.error(e_m)
            raise ValueError(e_m)
    return filtered

# Filter the intention list to only include entries with selected ids.
def intention_filter(intentions: list, ids: set | None) -> list[dict]:
    """
    Filter the intention list to only include entries with selected ids.
    Args:
        intentions: Original intentions in format [{"intention_id":"001" ...}...]
        ids: Set of selected ids (e.g., {"001", "003"})

    Returns:
        Filtered list containing only the specified intention dicts.
        If there is no ids input, the filtered list is empty.

    Raises:
        ValueError: If any id is not found in the list.
    """
    if not ids:
        return []

    # Build lookup dict: O(n)
    intention_map = {i["intention_id"]: i for i in intentions}

    # Find missing IDs: O(k)
    missing = [i for i in ids if i not in intention_map]
    if missing:
        e_m = f"以下意图id不存在：{missing}"
        logger_chatflow.error(e_m)
        raise ValueError(e_m)

    # Build filtered list in the same order as input IDs
    filtered = [intention_map[i] for i in ids]
    return filtered

# Convert dict in reply_content_info to actual string of reply
def process_reply(content_info_dict:dict, user_input: str):
    # Get the values from the content
    dialog_id = content_info_dict.get("dialog_id")
    content = content_info_dict.get("content")
    variate = content_info_dict.get("variate")
    reply_content = copy.deepcopy(content)

    if variate: # There are dynamic variates
        if not isinstance(variate, dict):
            e_m = f"variate应为字典"
            logger_chatflow.error(e_m)
            raise TypeError(e_m)
        for k, v in variate.items():
            if not isinstance(k, str):
                e_m = f"{k}应为字符串"
                logger_chatflow.error(e_m)
                raise TypeError(e_m)
            if not k in content:
                e_m = f"{content}中不含有variate的键{k}"
                logger_chatflow.error(e_m)
                raise TypeError(e_m)
            if not isinstance(v, dict):
                e_m = f"{v}应为字典"
                logger_chatflow.error(e_m)
                raise TypeError(e_m)

            # Process the variate
            if int(v.get("content_type")) == 2: #动态变量
                dynamic_var_set_type = int(v.get("dynamic_var_set_type"))
                if dynamic_var_set_type == 0: # 未开启动态变量赋值
                    reply_content = reply_content.replace(k, "")
                elif dynamic_var_set_type == 1: # 常量赋值
                    reply_content = reply_content.replace(k, v.get("value", ""))
                elif dynamic_var_set_type == 2: # 原话采集
                    reply_content = reply_content.replace(k, user_input)
                else:
                    e_m = f"{v}中的dynamic_var_set_type的值有误"
                    logger_chatflow.error(e_m)
                    raise ValueError(e_m)
    return dialog_id, content, variate, reply_content

# Update the target node id when setting up edges
def update_target(target: str, lookup: dict[str, str]) -> str:
    if target in lookup:
        target = lookup[target] # Convert target node id when switching main flow
    return f"{target}_reply"

# Find next main flow ids in the chatflow design
def next_main_flow(main_flow_id:str, sort_lookup:dict) -> str|None:
    """
    Get the next main flow ID in sequence.
    Args:
        main_flow_id: Current main flow ID
        sort_lookup: Dictionary mapping flow IDs to sort order values
    Returns:
        Next main flow ID or None if current is last
    """
    if not main_flow_id:
        e_m = f"当前流程ID为空"
        logger_chatflow.error(e_m)

    if not sort_lookup:
        e_m = f"主流程顺序表有误"
        logger_chatflow.error(e_m)

    if main_flow_id not in sort_lookup:
        e_m = f"当前流程{main_flow_id}不在设计内"
        logger_chatflow.error(e_m)

    current_order = sort_lookup.get(main_flow_id)
    candidate_flows = {
        flow_id: value
        for flow_id, value in sort_lookup.items()
        if value > current_order
    }

    # Check if current flow is the last one
    if not candidate_flows:
        return None

    # Get the key with the smallest order
    return min(candidate_flows, key=candidate_flows.get)

# Get last user log
def get_last_user_log_index(logs: list):
    if not isinstance(logs, list):
        e_m = f"logs应该为列表，不是 {type(logs).__name__}"
        logger_chatflow.error(e_m)

    for i in range(len(logs)-1, -1, -1):
        if isinstance(logs[i], dict) and logs[i].get("role") == "user":
            return i
    return None

def get_last_user_log(logs: list):
    last_user_idx = get_last_user_log_index(logs)
    if last_user_idx is not None:
        return logs[last_user_idx]
    return None

def get_logs_from_last_user(logs:list):
    last_user_idx = get_last_user_log_index(logs)
    if last_user_idx is not None:
        return logs[last_user_idx:]
    return logs[:]

# Node starting/ending work logging
def node_starting_logging(config: NodeConfig, thread_id: str):
    logger_chatflow.info("系统消息：%s", f"会话{thread_id}，节点{config.node_id}-{config.node_name}，开始工作")

def node_ending_logging(config:NodeConfig, thread_id: str, time_cost: float|None = None):
    if time_cost is not None:
        logger_chatflow.info("系统消息：%s", f"会话{thread_id}，节点{config.node_id}-{config.node_name}，完成工作，耗时{time_cost}秒")
    else:
        logger_chatflow.info("系统消息：%s", f"会话{thread_id}，节点{config.node_id}-{config.node_name}，完成工作")