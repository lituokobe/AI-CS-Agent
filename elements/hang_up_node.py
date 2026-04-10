from common.logger import setup_logger
from functionals.state import ChatState

logger = setup_logger('hang_up_node', category='hang_up_node', console_output=True)

# Function for the hang_up node in every project
def hang_up(state: ChatState) -> dict:
    log_info = "智能客服已挂断电话"
    logger.info("系统消息：%s", log_info)
    return {
        "messages": state["messages"],
        "dialog_state": None,
        "logs": state["logs"],
        "metadata": state["metadata"]
    }