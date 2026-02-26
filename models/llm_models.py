from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI

ALI_BASE_URL= "https://dashscope.aliyuncs.com/compatible-mode/v1"
ALI_API_KEY = ""

DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
DEEPSEEK_API_KEY = "sk-f952f77c672b48eda62fe9a15780a85d"

GLM_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"
GLM_API_KEY = ""

qwen_turbo = ChatOpenAI(
    model = 'qwen-turbo',
    temperature = 0,
    api_key = ALI_API_KEY,
    base_url = ALI_BASE_URL,
    max_tokens = 500,
    model_kwargs={"response_format": {"type": "json_object"}}
)

qwen_flash = ChatOpenAI(
    model = 'qwen-flash',
    temperature = 0,
    api_key = ALI_API_KEY,
    base_url = ALI_BASE_URL,
    max_tokens = 500,
    model_kwargs={"response_format": {"type": "json_object"}}
)

qwen_max = ChatOpenAI(
    # model = 'qwen-plus',
    model = 'qwen-max',
    temperature = 0,
    api_key = ALI_API_KEY,
    base_url = ALI_BASE_URL,
    max_tokens = 500,
    model_kwargs={"response_format": {"type": "json_object"}}
)

deepseek_llm = ChatOpenAI(
    model = 'deepseek-chat',
    # model='deepseek-reasoner',
    temperature = 0,
    api_key = DEEPSEEK_API_KEY,
    base_url = DEEPSEEK_BASE_URL,
    max_tokens = 100,
    model_kwargs={"response_format": {"type": "json_object"}}
)

glm_llm = ChatOpenAI(
    # model = 'glm-4.5',
    model = 'glm-4.6',
    temperature = 0,
    api_key = GLM_API_KEY,
    base_url = GLM_BASE_URL,
    max_tokens = 100,
    model_kwargs={"response_format": {"type": "json_object"}}
)

local_llm = ChatOpenAI(
    # ollama deployment
    # model='qwen3:8b',
    # model = "deepseek-r1:8b",
    # model="qwen2.5:latest",

    # vllm deployment
    # model="Qwen2-7B-Instruct-AWQ",
    # model="Qwen2.5-7B-Instruct-AWQ",
    # model="Qwen2.5-3B-Instruct-GPTQ-Int4",
    model="Qwen3-8B-AWQ",
    # model="qwen3-8b",

    # other arguments
    temperature=0,
    # base_url='http://192.168.0.143:8000/v1',
    base_url='http://127.0.0.1:8000/v1',
    api_key = "none",
    max_tokens=100,
    timeout=60,
    model_kwargs={"response_format": {"type": "json_object"}}
)

if __name__ == '__main__':
    test_messages = [
        HumanMessage(content='',
                     additional_kwargs={},
                     response_metadata={},
                     id='e5f1a79e-b4f7-4cbd-8483-9dc92f8eee95'
                     ),
        AIMessage(content='喂您好，（停顿2秒）我是巨峰科技的客服，近期我们针对汤臣一品业主举办了一个关于老房子翻新，毛坯房设计，和局部改动的实景样板房体验展，如果您近期或者明年有装修计划的话，都可以到现场免费的咨询了解一下',
                  additional_kwargs={},
                  response_metadata={},
                  id='0bbcf2fa-7dd4-4c93-9e97-95dfeb87c1a6'
                  ),
        HumanMessage(content='有这方面的打算',
                     additional_kwargs={},
                     response_metadata={},
                     id='caccf4b0-6fd9-4a77-996f-ed809667dc4b'
                     )
    ]
    response = qwen_turbo.invoke(test_messages)
    print(response)