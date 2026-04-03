import asyncio

from functionals.log_utils import logger_chatflow
from functionals.matchers import KeywordMatcher, SemanticMatcher

# Combine the intention keyword matcher and the knowledge keyword matcher based on user's preference of intention_priority
class IntegratedKeywordsMatcher:
    def __init__(self,
                 intention_priority:int,
                 keyword_matcher:KeywordMatcher,
                 knowledge_keyword_matcher:KeywordMatcher):
        self.keyword_matcher = keyword_matcher
        self.knowledge_keyword_matcher = knowledge_keyword_matcher
        if intention_priority == 2:
            self._match_strategy = self._match_intention_first
        elif intention_priority == 1:
            self._match_strategy = self._match_knowledge_first
        elif intention_priority == 3:
            self._match_strategy = self._match_integrated
        else:
            e_m = "优先选择仅能为‘1-知识库优先’，‘2-回答分支优先’或‘3-智能匹配优先’"
            logger_chatflow.error(e_m)
            raise ValueError(e_m)

    def match(self, user_input:str):
        """
        Infer user intention based on integrated keyword matching.
        Returns: (type_id, type_name, keywords, count, inference_type)
        """
        return self._match_strategy(user_input)

    # Define a function to match the user input with inference type output
    def _try_match(self, matcher: KeywordMatcher, inference_label: str, user_input: str):
        result = matcher.analyze_sentence(user_input)
        if result:
            type_id, type_name, keywords, count = matcher.get_primary_type(result)
            return type_id, type_name, keywords, count, inference_label
        return None

    def _match_intention_first(self, user_input: str):
        match = self._try_match(self.keyword_matcher, "意图库", user_input)
        if match:
            return match
        return (self._try_match(self.knowledge_keyword_matcher, "知识库", user_input)
                or ("", "", [], 0, "无"))

    def _match_knowledge_first(self, user_input: str):
        match = self._try_match(self.knowledge_keyword_matcher, "知识库", user_input)
        if match:
            return match
        return (self._try_match(self.keyword_matcher, "意图库", user_input) or
                ("", "", [], 0, "无"))

    def _match_integrated(self, user_input: str):
        intention_result = self.keyword_matcher.analyze_sentence(user_input)
        knowledge_result = self.knowledge_keyword_matcher.analyze_sentence(user_input)

        if not intention_result and not knowledge_result:
            return "", "", [], 0, "无"

        integrated_result = intention_result | knowledge_result  # union of matches

        type_id, type_name, keywords, count = self.keyword_matcher.get_primary_type(integrated_result)
        inference_type = "知识库" if type_id in knowledge_result else "意图库"
        return type_id, type_name, keywords, count, inference_type

class IntegratedSemanticMatcher:
    def __init__(self,
                 nlp_threshold:float,
                 intention_priority: int,
                 semantic_matcher:SemanticMatcher,
                 knowledge_semantic_matcher:SemanticMatcher):
        self.nlp_threshold = nlp_threshold
        self.semantic_matcher = semantic_matcher
        self.knowledge_semantic_matcher = knowledge_semantic_matcher

        if intention_priority == 2:
            self._match_strategy = self._match_intention_first
        elif intention_priority == 1:
            self._match_strategy = self._match_knowledge_first
        elif intention_priority == 3:
            self._match_strategy = self._match_integrated
        else:
            e_m = "优先选择仅能为‘1-知识库优先’，‘2-回答分支优先’或‘3-智能匹配优先’"
            logger_chatflow.error(e_m)
            raise ValueError(e_m)

    async def match(self, user_input: str):
        """
        Infer user intention using semantic similarity.
        Returns: (type_id, type_name, content, cos_score, inference_type)
        """
        return await self._match_strategy(user_input)

    async def _match_intention_first(self, user_input: str):
        # Use semantic matcher match first
        tid_i, tname_i, cont_i, score_i = await self.semantic_matcher.find_most_similar(user_input)
        if score_i > self.nlp_threshold:
            return tid_i, tname_i, cont_i, score_i, "意图库"
        # If not successful, use knowledge matcher match
        else:
            tid_k, tname_k, cont_k, score_k = await self.knowledge_semantic_matcher.find_most_similar(user_input)
            if score_k > self.nlp_threshold:
                return tid_k, tname_k, cont_k, score_k, "知识库"
            # If still not successful, return the result with highest score
            else:
                if score_i>score_k:
                    return tid_i, tname_i, cont_i, score_i, "无"
                else:
                    return tid_k, tname_k, cont_k, score_k, "无"

    async def _match_knowledge_first(self, user_input: str):
        # Use knowledge matcher match first
        tid_k, tname_k, cont_k, score_k = await self.knowledge_semantic_matcher.find_most_similar(user_input)
        if score_k > self.nlp_threshold:
            return tid_k, tname_k, cont_k, score_k, "知识库"
        # If not successful, use semantic matcher match
        else:
            tid_i, tname_i, cont_i, score_i = await self.semantic_matcher.find_most_similar(user_input)
            if score_i > self.nlp_threshold:
                return tid_i, tname_i, cont_i, score_i, "意图库"
            # If still not successful, return the result with highest score
            else:
                if score_i > score_k:
                    return tid_i, tname_i, cont_i, score_i, "无"
                else:
                    return tid_k, tname_k, cont_k, score_k, "无"

    async def _match_integrated(self, user_input: str):
        DEFAULT_RESULT = ("", "", "", 0.0)
        # Run both matches concurrently
        tasks = [
            self.semantic_matcher.find_most_similar(user_input),
            self.knowledge_semantic_matcher.find_most_similar(user_input)
        ]
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=3.0
            )
            intention_result, knowledge_result = results

            # Normalize exceptions to default result
            if isinstance(intention_result, Exception):
                logger_chatflow.error(f"意图库语义匹配异常: {intention_result}")
                intention_result = DEFAULT_RESULT
            if isinstance(knowledge_result, Exception):
                logger_chatflow.error(f"知识库语义匹配异常: {knowledge_result}")
                knowledge_result = DEFAULT_RESULT

        except asyncio.TimeoutError:
            logger_chatflow.warning("语义匹配超时（3秒）")
            intention_result = knowledge_result = DEFAULT_RESULT

        tid_i, tname_i, cont_i, score_i = intention_result if intention_result else DEFAULT_RESULT
        tid_k, tname_k, cont_k, score_k = knowledge_result if knowledge_result else DEFAULT_RESULT

        if score_i>score_k:
            if score_i > self.nlp_threshold:
                return tid_i, tname_i, cont_i, score_i, "意图库"
            else:
                return tid_i, tname_i, cont_i, score_i, "无"
        else:
            if score_k > self.nlp_threshold:
                return tid_k, tname_k, cont_k, score_k, "知识库"
            else:
                return tid_k, tname_k, cont_k, score_k, "无"