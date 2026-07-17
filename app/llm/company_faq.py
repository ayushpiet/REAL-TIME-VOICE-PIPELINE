"""
company_faq.py

Loads company FAQ knowledge base and formats it as a text block
that can be appended to VOICE_SYSTEM_PROMPT, so the LLM can answer
company-related customer questions accurately instead of guessing.

Usage:
    from app.llm.company_faq import get_faq_context_block
    full_prompt = VOICE_SYSTEM_PROMPT + "\n\n" + get_faq_context_block()
"""

import json
from pathlib import Path

_FAQ_PATH = Path(__file__).parent / "knowledge_base.json"


def load_faq_data() -> dict:
    """Load the raw FAQ JSON data from disk."""
    with open(_FAQ_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_faq_context_block() -> str:
    """
    Build a single text block of all company Q&A pairs, formatted for
    injection into the LLM system prompt. Keep this appended AFTER
    VOICE_SYSTEM_PROMPT so tone/style instructions still take priority.
    """
    data = load_faq_data()
    company_name = data.get("company_name", "the company")

    lines = [
        f"COMPANY KNOWLEDGE BASE — {company_name}",
        "Use the following verified information to answer customer questions "
        "about the company. If a caller asks something not covered here, "
        "don't guess — instead say you don't have that specific detail, and "
        "offer to take their Name and Phone number so the team can reach out to them.",
        "",
    ]

    for section in data.get("faqs", []):
        category = section.get("category", "General")
        lines.append(f"## {category}")
        for pair in section.get("qa", []):
            lines.append(f"Q: {pair['q']}")
            lines.append(f"A: {pair['a']}")
        lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    # Quick manual check: print the formatted block
    print(get_faq_context_block())