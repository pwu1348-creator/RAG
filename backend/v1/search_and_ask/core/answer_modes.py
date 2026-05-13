"""
回答风格预设（answer mode presets）

两种预设模板，覆盖 LLM 采样参数 + 检索参数 + 系统提示词后缀：
- strict（严谨）: 知识库 / 规章 / 法规 / 原文作答场景
- loose  （宽松）: 闲聊 / 改写 / 扩写 / 娱乐场景

前端通过 `answer_mode` 字段在每次问答请求时指定，后端根据该字段
从本文件读取对应 preset 并解构到 LLM 请求体和检索调用中。
"""

from typing import Dict, Any, Literal


AnswerMode = Literal["strict", "loose"]


STRICT_PRESET: Dict[str, Any] = {
    "llm": {
        "temperature": 0.3,
        "top_p": 0.7,
        "top_k": 20,
        "frequency_penalty": 3.0,
        "enable_thinking": True,
    },
    "retrieval": {
        "bm25_weight": 0.5,
        "vector_weight": 0.5,
        "min_score": 0.4,
        "top_k": 10,
        "use_rerank": True,
        "use_kg": True,
        "kg_weight": 0.3,
    },
    "system_suffix": (
        "请严格按照文档原文作答，不允许外推或猜测，"
        "所有结论必须来自检索结果。"
    ),
}


LOOSE_PRESET: Dict[str, Any] = {
    "llm": {
        "temperature": 0.6,
        "top_p": 0.9,
        "top_k": 50,
        "frequency_penalty": 0.3,
        "enable_thinking": True,
    },
    "retrieval": {
        "bm25_weight": 0.7,
        "vector_weight": 0.3,
        "min_score": 0.2,
        "top_k": 10,
        "use_rerank": True,
        "use_kg": True,
        "kg_weight": 0.3,
    },
    "system_suffix": (
        "可以基于文档进行合理引申和补充，"
        "但要明确区分哪些是文档原文、哪些是补充观点。"
    ),
}


PRESETS: Dict[str, Dict[str, Any]] = {
    "strict": STRICT_PRESET,
    "loose": LOOSE_PRESET,
}

DEFAULT_MODE: AnswerMode = "strict"


def get_preset(mode: str) -> Dict[str, Any]:
    """按名称获取 preset，未知 mode 回退到默认。"""
    return PRESETS.get(mode, PRESETS[DEFAULT_MODE])
