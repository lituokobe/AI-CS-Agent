import asyncio
import json
import os
import redis.asyncio as redis_async
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.redis import AsyncRedisSaver
from agent_builders.chatflow_builder import build_chatflow
from config.config_setup import ChatFlowConfig
from config.db_setting import DBSetting
# from data.simulated_data_lt import agent_data, knowledge, knowledge_main_flow, chatflow_design, global_configs, intentions
from data.simulated_data_lt_simplified import agent_data, knowledge, knowledge_main_flow, chatflow_design, global_configs, intentions
# from data.simulated_data import agent_data, knowledge, knowledge_main_flow, chatflow_design, global_configs, intentions
# from data.simulated_data_xyp20251222 import agent_data, knowledge, knowledge_main_flow, chatflow_design, global_configs, intentions
from functionals.log_utils import logger_chatflow

# The function to run the chatflow
async def main(call_id: str, fresh_start: bool = True):
    # Initialize chatflow config
    chatflow_config = ChatFlowConfig.from_files(
        agent_data,
        knowledge,
        knowledge_main_flow,
        chatflow_design,
        global_configs,
        intentions
    )
    # Initialize conv_config
    conv_config = {"configurable": {"thread_id": call_id}}
    """
    "configurable" and "thread_id" are a convention used by LangGraph’s checkpointer to identify a conversation.
    In the dict of "configurable", more customized keys like "user_id" can be added.
    We use plain dict to play as conv_config. RunnableConfig is the built-in class to serve this purpose.
    But for the annotation of the node's __call__ function, we need to annotate config: RunnableConfig or keep it unannotated.
    Annotating it as dict or ANY will lead to error, even if it is a dict.
    """
    # TODO: Setup redis_client
    settings = DBSetting()
    redis_client = redis_async.Redis( #异步Redis
        #get redis server url from env (for Docker) first, if not, get it from settings
        host=os.getenv("REDIS_SERVER", settings.REDIS_SERVER),
        password=settings.REDIS_PASSWORD,
        port=int(settings.REDIS_PORT),
        db=settings.REDIS_DB, # Redis Search requires index be built on database 0
        decode_responses=False, #Let Redis reserve the binary data, instead converting it to Python strings
        max_connections=50
    )
    redis_checkpointer = AsyncRedisSaver(redis_client=redis_client)
    await redis_checkpointer.setup()  # Async setup

    # Remove history from the call ID
    if fresh_start:
        await redis_checkpointer.adelete_thread(call_id)
        logger_chatflow.info("系统消息：%s", f"{call_id}新对话")
    else:
        logger_chatflow.info("系统消息：%s", f"{call_id}重启对话")

    # TODO: Build chatflow and get milvus_client
    chatflow, milvus_client = await build_chatflow(chatflow_config, redis_checkpointer=redis_checkpointer)

    # TODO: User talk to the agent
    print("=== 智能客服已上线 ===\n")

    # Step 1: Use empty input to trigger welcome message
    # LangGraph accepts dict as config, and will automatically convert it to a RunnableConfig internally if needed.
    state = await chatflow.ainvoke({"messages": [HumanMessage(content="")]}, config=conv_config)

    # Print initial assistant message
    messages = state.get("messages")
    if messages:
        if isinstance(messages, list):
            last_msg = messages[-1]
            if last_msg.__class__.__name__ == "AIMessage":
                print(f"智能客服：{last_msg.content}")

    print()
    # Step 2: Main conversation loop
    while True:
        # Get user input
        user_input = input("用户：").strip()
        if user_input == "挂电话":
            log_info = "用户已挂断电话"
            logger_chatflow.info("系统消息：%s", log_info)
            break

        # Record current state BEFORE processing
        prev_msg_count = len(state["messages"])
        # Create user message
        new_user_message = {"messages": [HumanMessage(content=user_input)]}

        # Resume workflow
        try:
            state = await chatflow.ainvoke(new_user_message, config=conv_config) # invoke is best for call-bot, stream for text-bot
        except Exception as e:
            logger_chatflow.error("系统错误：%s", {e})
            break

        # Get ONLY new messages and metadata generated in this turn
        new_messages = state["messages"][prev_msg_count:]

        # Print all new assistant messages with their metadata
        for idx, msg in enumerate(new_messages):
            if msg.__class__.__name__ == "AIMessage":
                print(f"智能客服：{msg.content}")  # Use .content, not ['content']
        print()  # Extra newline after all messages

    # TODO: Close the async clients
    await milvus_client.close()
    await redis_client.aclose()

    return state

if __name__ == "__main__":
    state = asyncio.run(main("test_call"))

    # Export state
    export_state = False
    if export_state:
        def convert(obj):
            if isinstance(obj, set):
                return list(obj)
            return str(obj)  # fallback for other non-serializable types
        with open("chat_state.json", "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2, default=convert)

    # Print final messages
    print("=== 智能客服已下线 ===")
    print("聊天记录：")
    for msg in state["messages"]:
        if msg.__class__.__name__ == "AIMessage":
            print(f"智能客服：{msg.content}")
        if msg.__class__.__name__ == "HumanMessage":
            print(f"用户：{msg.content}")
    print("-"*50)
    print("状态历史：")
    print(state["dialog_state"])
    print("-" * 50)
    print("元数据：")
    for metadata in state["metadata"]:
        print(metadata)
    print("-" * 50)
    print("LOGS：")
    for log in state["logs"]:
        print(log)