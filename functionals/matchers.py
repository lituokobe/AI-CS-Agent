from typing import Any
import re
from functionals.log_utils import logger_chatflow
from config.config_setup import NodeConfig

# Keyword approach
import ahocorasick

# Semantic approach
from pymilvus import MilvusClient, AsyncMilvusClient
from functionals.embedding_functions import embed_query

# LLM approach
from models.llm_models import qwen_turbo, qwen_flash, qwen_max, deepseek_llm, glm_llm, local_llm
from data.string_asset import docstring_base_raw, priority_map, docstring_tail
from langchain_core.messages import HumanMessage
import ast

"""
3 type of matchers:
KeywordMatcher, based on keyword detection to have user's intention
SemanticMatcher, based on vector semantic matching to have user's intention
LLMInferenceMatcher, based on LLM's inference to have user's intention

KeywordMatcher.get_primary_type(), SemanticMatcher.find_most_similar(), LLMInferenceMatcher.llm_infer()
will all return 5 values:
- user's intention id
- user's intention type
- inference type: 意图库, 知识库, 无
- extra info 1
- extra info 2 (Optional)

"""

# TODO: Create a keyword matching class, supporting regular expression
# Below method is using ahocorasick, which provide perfect isolation and faster speed.
class KeywordMatcher:
    def __init__(self, intentions: list):
        self.intentions = intentions
        self.keyword_to_id_and_type = {}
        self.all_keywords = set()
        self.regex_patterns = []  # List of tuples: (compiled_regex, original_pattern, intention_id, intention_name)
        self.automaton = None
        if intentions:
            self.load_keywords_from_dict(intentions)

    @staticmethod
    def _is_probably_regex(pattern: str) -> bool:
        """
        Heuristic to detect if a string is intended as a regex.
        You can adjust this logic if needed (e.g., require explicit flag).
        """
        regex_meta = {'^', '$', '|', '(', ')', '*', '+', '?', '[', '{', '\\'}
        return any(char in regex_meta for char in pattern)

    def load_keywords_from_dict(self, intentions: list):
        self.keyword_to_id_and_type.clear()
        self.all_keywords.clear()
        self.regex_patterns.clear()

        for intention in intentions:
            self.add_keyword_list(
                intention["intention_id"],
                intention["intention_name"],
                intention["keywords"]
            )
        self._build_automaton()

    def add_keyword_list(self, intention_id: str, intention_name: str, keywords: list[str] | None):
        if not keywords:
            return
        for keyword in keywords:
            keyword = keyword.strip()
            if not keyword:
                continue
            if self._is_probably_regex(keyword):
                # Store compiled regex + metadata
                try:
                    compiled = re.compile(keyword)
                    self.regex_patterns.append((compiled, keyword, intention_id, intention_name))
                except re.error:
                    # Optionally log or skip invalid regex
                    continue
            else:
                if keyword not in self.all_keywords:
                    self.keyword_to_id_and_type[keyword] = (intention_id, intention_name)
                    self.all_keywords.add(keyword)

    def _build_automaton(self):
        if not self.all_keywords:
            self.automaton = None
            return
        A = ahocorasick.Automaton()
        for keyword in self.all_keywords:
            A.add_word(keyword, keyword)
        A.make_automaton()
        self.automaton = A

    def analyze_sentence(self, sentence: str) -> dict[str, dict[str, Any]]:
        result = {}

        # 1. Match literal keywords using Aho-Corasick
        if self.automaton:
            for end_index, keyword in self.automaton.iter(sentence):
                intention_id, keyword_type = self.keyword_to_id_and_type[keyword]
                if intention_id not in result:
                    result[intention_id] = {
                        "keyword_type": keyword_type,
                        "count": 0,
                        "keywords": []
                    }
                result[intention_id]["count"] += 1
                result[intention_id]["keywords"].append(keyword)

        # 2. Match regex patterns
        for compiled_regex, original_pattern, intention_id, keyword_type in self.regex_patterns:
            # Use finditer to find all non-overlapping matches
            matches = list(compiled_regex.finditer(sentence))
            if matches:
                if intention_id not in result:
                    result[intention_id] = {
                        "keyword_type": keyword_type,
                        "count": 0,
                        "keywords": []
                    }
                count = len(matches)
                result[intention_id]["count"] += count
                # Append the original regex pattern once per match (as requested)
                result[intention_id]["keywords"].extend([original_pattern] * count)
        return result

    @staticmethod
    def get_primary_type(result: dict[str | None, dict[str, Any] | None]) -> tuple[str, str, list[str], int]:
        if not result:
            e_m = "输入的关键词查询结果为空"
            logger_chatflow.error(e_m)
            return "others", "", [], 0

        primary_id = max(result.keys(), key=lambda k: result[k]['count'])
        info = result[primary_id]
        return primary_id, info["keyword_type"], info["keywords"], info["count"]

# TODO: Create a semantic matching class
class SemanticMatcher:
    def __init__(self,
                 collection_name: str,
                 intention_ids: set|list,
                 milvus_client: MilvusClient | AsyncMilvusClient | None = None):
        self.collection_name = collection_name
        self.milvus_client = milvus_client
        self.intention_ids = intention_ids

    async def find_most_similar(self, sentence: str) -> tuple[str, str, str, float]:
        """
        Find the most similar intention to the given sentence.

        Returns:
            tuple: (intention_id, intention_name, phrase, similarity_score)
            Always returns a valid tuple even when no match is found
        """
        DEFAULT_RESULT = ("", "", "", 0.0)
        if not self.intention_ids:
            return DEFAULT_RESULT

        try:
            # Generate query embedding
            query_emb = embed_query(sentence)
            if hasattr(query_emb, 'tolist'):
                query_emb = query_emb.tolist()

            # Build filter expression: intention_id in ["K003", "I008", ...], Milvus uses string expressions
            id_list_str = ",".join(f'"{id_}"' for id_ in self.intention_ids)
            filter_expr = f"intention_id in [{id_list_str}]"

            # Perform search
            results = await self.milvus_client.search(
                collection_name=self.collection_name,
                data=[query_emb],
                filter=filter_expr,
                limit=1,
                output_fields=["intention_id", "intention_name", "phrase"],
                timeout = 3.0
            )

            # Check if we have results
            if not results or not results[0]:
                return DEFAULT_RESULT

            # Extract result safely
            hit = results[0][0] # hit is a Milvus hit object, similar to dict
            entity = hit.get("entity", {})

            return (entity.get("intention_id", ""), entity.get("intention_name", ""),
                entity.get("phrase", ""), hit.get("distance", 0.0))

        except Exception as e:
            logger_chatflow.error(f"'{sentence}'查询失败: {str(e)}", exc_info=True)
            # Final fallback
            return DEFAULT_RESULT

# TODO: Create a LLM inference matching class
class LLMInferenceMatcher:
    def __init__(self,
                 config: NodeConfig,
                 intentions: list,
                 knowledge_infer_name: dict,
                 knowledge_infer_description: dict,
                 intention_priority: int):
        self.config = config
        self.intention_infer_name = {} # dict: intention_id -> intention_name
        self.intention_infer_descriptions = {} # dict: intention_id -> intention_name - intention_description
        if intentions:
            for intention in intentions:
                self.intention_infer_name[intention["intention_id"]] = intention["intention_name"]
                intention_description = " ".join(intention["llm_description"]) if intention["llm_description"] else "无意图说明"
                self.intention_infer_descriptions[intention["intention_id"]] = str(intention["intention_name"]) + " - " + intention_description

        # remove the knowledge item that user specifically ask not to include via "nomatch_knowledge_ids"
        nomatch_knowledge_ids = self.config.other_config.get("nomatch_knowledge_ids", [])
        if not isinstance(nomatch_knowledge_ids, list):
            e_m = f"{config.node_id}-{config.node_name}节点nomatch_knowledge_ids应为列表"
            logger_chatflow.error(e_m)
            raise TypeError(e_m)
        self.knowledge_infer_name = {k:v for k, v in knowledge_infer_name.items() if k not in nomatch_knowledge_ids} # dict to store knowledge intention_id: intention_name
        self.knowledge_infer_description = {k:v for k, v in knowledge_infer_description.items() if k in self.knowledge_infer_name} # dict to store knowledge intention_id : intention_name - intention_description

        # background prompt
        self.llm_role_description: str = getattr(config.agent_config, "llm_role_description", "")
        self.llm_background_info: str = getattr(config.agent_config, "llm_background_info", "")

        # prompts
        self.base_docstring: list = self._create_base_docstring(intention_priority) or []

        # select llm runnable
        self.llm_runnable = self._select_llm(config.agent_config.llm_name)

    @staticmethod
    def _select_llm(llm_name: str):
        if llm_name == "qwen_turbo":
            return qwen_turbo
        elif llm_name == "qwen_flash":
            return qwen_flash
        elif llm_name == "qwen_max":
            return qwen_max
        elif llm_name == "local_llm":
            return local_llm
        elif llm_name == "deepseek_llm":
            return deepseek_llm
        elif llm_name == "glm_llm":
            return glm_llm
        return qwen_turbo

    def _create_base_docstring(self, intention_priority: int) -> list:
        """
        Prepare the base docstring from the LLM
        """
        #Add intention priority
        docstring_base = (
                [
                    "## === 你的角色描述和背景信息（仅供参考） ===",
                    self.llm_role_description,
                    self.llm_background_info,
                    ""
                ] +
                docstring_base_raw +
                [priority_map[intention_priority]] + priority_map[4:]
        )

        # Include the intention descriptions
        docstring_base.append("**【意图库列表】**（- 意图id : 意图名称 - 意图说明）")
        if self.intention_infer_descriptions:
            for k, v in self.intention_infer_descriptions.items():
                docstring_base.append(f"  - {k} : {v}")
        else:
            docstring_base.append("")

        docstring_base.append("")
        docstring_base.append("**【知识库列表】**（- 意图id : 意图名称 - 意图说明）")
        if self.knowledge_infer_description: # if knowledge exists
            for k, v in self.knowledge_infer_description.items():
                docstring_base.append(f"  - {k} : {v}")
        else: # if knowledge doesn't exist, append an empty string as a blank row later
            docstring_base.append("")
        docstring_base.append("")

        return docstring_base

    @staticmethod
    def _parse_llm_json_output(text: str) -> tuple[str, str]:
        """
        Parse LLM output robustly. Always returns (input_summary, intention_id).
        """
        text = text.strip()

        if text.startswith("```"):
            text = re.split(r"```(?:json)?", text, maxsplit=1)[-1]
            text = text.rsplit("```", 1)[0] if "```" in text else text
        text = text.strip()

        # Try to parse
        try:
            data = ast.literal_eval(text)
            if isinstance(data, dict):
                summary = str(data.get("input_summary", "无"))[:10]
                id_ = str(data.get("intention_id", "others"))
            else:
                summary, id_ = "无", "others"
        except Exception as e:
            logger_chatflow.error("大模型输出解析异常：%s", {e})
            # Fallback: extract using regex
            summary_match = re.search(r'[\'"`]input_summary[\'"`]\s*:\s*[\'"`](.*?)[\'"`]', text)
            summary = summary_match.group(1)[:10] if summary_match else "无"

            id_match = re.search(r'[\'"`]intention_id[\'"`]\s*:\s*[\'"`](.*?)[\'"`]', text)
            id_ = id_match.group(1) if id_match else "others"

        return summary, id_

    async def llm_infer(self, chat_history: list, user_input: str) -> tuple[str, str, str, str, int]:
        """
        Infer the user intention from the user input.
        """
        if not self.llm_runnable:
            e_m = "LLM推理工具未初始化"
            logger_chatflow.error(e_m)

        # Initialize default values
        intention_id, user_intention, input_summary, inference_type, token_used = (
            "others", "其他", "无", "无", 0
        )
        try:
            # Create prompt of chat history
            docstring_chat_history = []
            for msg in chat_history:
                if msg.__class__.__name__ == "HumanMessage":
                    docstring_chat_history.append(f"- 【用户】{msg.content}")
                elif msg.__class__.__name__ == "AIMessage":
                    ai_message = msg.content
                    if ai_message:
                        docstring_chat_history.append(f"- 【智能助手】{ai_message}")
            docstring_chat_history.append("")

            # Create full prompt
            full_docstring = (self.base_docstring +
                              [
                                  "### **最后一次用户输入**",
                                  user_input,
                                  "",
                                  "### 智能助手和用户的对话历史（务必参考）"
                              ] +
                              docstring_chat_history +
                              docstring_tail)
            full_prompt = "\n".join(full_docstring)
            print(f"{self.config.node_id}-{self.config.node_name}节点的大模型提示词 \n{full_prompt}")
            print()
            # Invoke the llm
            resp = await self.llm_runnable.ainvoke([HumanMessage(content=full_prompt)])

            # Get the tokens consumed per round of conversation including the preconfigured doc string, full chat history, AI reply, etc.
            token_used = int(resp.response_metadata.get("token_usage", {}).get("total_tokens", 0))
            print(f"大模型回复内容： {resp}")
            input_summary, intention_id = self._parse_llm_json_output(resp.content)
        except Exception as e:
            logger_chatflow.error("LLM推理调用异常：%s", {e})

        if intention_id in self.intention_infer_name:
            user_intention = self.intention_infer_name[intention_id]
            inference_type = "意图库"
        elif intention_id in self.knowledge_infer_name:
            user_intention = self.knowledge_infer_name[intention_id]
            inference_type = "知识库"

        print(f"大模型回复处理后内容：intention_id: {intention_id}, user_intention: {user_intention}, "
              f"input_summary: {input_summary}, inference_type: {inference_type}")
        return intention_id, user_intention, input_summary, inference_type, token_used