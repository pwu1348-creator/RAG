
from typing import Dict, Any, Literal


AnswerMode = Literal["strict", "loose"]


STRICT_PRESET: Dict[str, Any] = {
    "llm": {
        "temperature": 0.3,
        "top_p": 0.7,
        "top_k": 20,
        "frequency_penalty": 0.5,
        "enable_thinking": True,
    },
    "retrieval": {
        "bm25_weight": 0.5,
        "vector_weight": 0.5,
        "min_score": 0.15,
        "top_k": 15,
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
        "min_score": 0.15,
        "top_k": 15,
        "use_rerank": True,
        "use_kg": True,
        "kg_weight": 0.3,
    },
    "system_prompt_override": (
        "你是一个有趣又靠谱的智能助手，既懂知识库里的专业内容，也能像朋友一样聊天。请遵守以下规则：\n"
        "1. 优先参考下方「检索结果」中的内容来回答用户问题，涉及文档事实时要准确；\n"
        "2. 如果检索结果不够完整或与问题关联不大，大胆结合自身知识进行补充和解释；\n"
        "3. 语气自然随和，可以适当幽默、口语化、带点个性，不用端着；\n"
        "4. 在陈述文档事实时保持准确，但在扩展解释、举例、类比时可以自由发挥；\n"
        "5. 禁止输出「根据检索结果」「根据以上内容」等生硬的元描述；\n"
        "6. 回答有条理就行，不必过于正式，像在跟用户面对面聊天一样。"
    ),
    "system_suffix": "",
}


PRESETS: Dict[str, Dict[str, Any]] = {
    "strict": STRICT_PRESET,
    "loose": LOOSE_PRESET,
}

DEFAULT_MODE: AnswerMode = "strict"


def get_preset(mode: str) -> Dict[str, Any]:
    return PRESETS.get(mode, PRESETS[DEFAULT_MODE])
