"""Lightweight heuristics for inferring the user's writing style."""

from __future__ import annotations

import re
from typing import Dict, List


DEFAULT_STYLE: Dict[str, str] = {
    "capitalization": "standard",
    "message_length": "medium",
    "emoji_usage": "minimal",
    "formality": "neutral",
}


def analyze_user_style(recent_messages: List[str]) -> Dict[str, str]:
    if not recent_messages:
        return dict(DEFAULT_STYLE)

    relevant_messages = [msg for msg in recent_messages if isinstance(msg, str) and msg.strip()]
    if not relevant_messages:
        return dict(DEFAULT_STYLE)

    style = dict(DEFAULT_STYLE)
    style["capitalization"] = _detect_capitalization(relevant_messages)
    style["message_length"] = _detect_message_length(relevant_messages)
    style["emoji_usage"] = _detect_emoji_usage(relevant_messages)
    style["formality"] = _detect_formality(relevant_messages)
    return style


def _detect_capitalization(messages: List[str]) -> str:
    total = 0
    lowercase = 0
    for message in messages[-10:]:
        sentences = re.split(r"[.!?\n]+", message)
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 5:
                continue
            total += 1
            first_alpha = next((char for char in sentence if char.isalpha()), None)
            if first_alpha and first_alpha.islower():
                lowercase += 1
    if total == 0:
        return "standard"
    ratio = lowercase / total
    if ratio >= 0.7:
        return "lowercase"
    if ratio >= 0.3:
        return "mixed"
    return "standard"


def _detect_message_length(messages: List[str]) -> str:
    word_counts = [len(message.split()) for message in messages[-10:]]
    if not word_counts:
        return "medium"
    avg_words = sum(word_counts) / len(word_counts)
    if avg_words < 10:
        return "ultra_short"
    if avg_words < 30:
        return "short"
    if avg_words < 100:
        return "medium"
    return "long"


EMOJI_REGEX = re.compile(
    "[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF"
    "\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF"
    "\U0001F900-\U0001F9FF\U0001FA00-\U0001FAFF\U00002702-\U000027B0]"
)


def _detect_emoji_usage(messages: List[str]) -> str:
    total_chars = 0
    emoji_count = 0
    for message in messages[-10:]:
        total_chars += len(message)
        emoji_count += len(EMOJI_REGEX.findall(message))
    if total_chars == 0:
        return "minimal"
    ratio = (emoji_count / total_chars) * 100
    if ratio == 0:
        return "none"
    if ratio < 2:
        return "minimal"
    if ratio < 5:
        return "moderate"
    return "heavy"


FORMAL_MARKERS = {
    "formal": (
        "здравствуйте",
        "добрый день",
        "уважаемый",
        "коллеги",
        "конструктив",
        "выполнить",
        "согласовать",
        "прошу",
    ),
    "casual": (
        "чел",
        "чувак",
        "бро",
        "лол",
        "хаха",
        "гы",
        "капец",
        "типа",
        "щас",
    ),
}


def _detect_formality(messages: List[str]) -> str:
    recent_text = " ".join(messages[-10:]).lower()
    if not recent_text:
        return "neutral"
    if any(marker in recent_text for marker in FORMAL_MARKERS["formal"]):
        return "formal"
    if any(marker in recent_text for marker in FORMAL_MARKERS["casual"]):
        return "casual"
    return "neutral"


